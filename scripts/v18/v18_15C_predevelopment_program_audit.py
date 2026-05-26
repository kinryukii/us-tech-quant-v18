from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_15C_PREDEVELOPMENT_PROGRAM_AUDIT_READY"
STATUS_WARN = "WARN_V18_15C_PREDEVELOPMENT_AUDIT_BLOCKERS_FOUND"
MODE = "READ_ONLY_PREDEVELOPMENT_AUDIT"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"

PS_PARSE_REQUIRED = [
    "scripts/v18/run_v18_current_daily_command_center.ps1",
    "scripts/v18/run_v18_15B_current_daily_with_manual_feedback.ps1",
    "scripts/v18/run_v18_15A_manual_position_trade_feedback.ps1",
    "scripts/v18/run_v18_14E_current_daily_with_forward_tracker.ps1",
    "scripts/v18/run_v18_14C_ranked_candidate_forward_tracker.ps1",
    "scripts/v18/run_v18_14D_ranked_candidate_forward_price_filler.ps1",
    "scripts/v18/run_v18_15C_predevelopment_program_audit.ps1",
]

PY_COMPILE_REQUIRED = [
    "scripts/v18/v18_15B_current_daily_with_manual_feedback.py",
    "scripts/v18/v18_15A_manual_position_trade_feedback.py",
    "scripts/v18/v18_14E_current_daily_with_forward_tracker.py",
    "scripts/v18/v18_14C_ranked_candidate_forward_tracker.py",
    "scripts/v18/v18_14D_ranked_candidate_forward_price_filler.py",
    "scripts/v18/v18_15C_predevelopment_program_audit.py",
]

CURRENT_ALIASES = [
    "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
    "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv",
    "outputs/v18/positions/V18_CURRENT_MANUAL_POSITION_REVIEW.csv",
    "outputs/v18/positions/V18_CURRENT_MANUAL_TRADE_FEEDBACK.csv",
    "outputs/v18/positions/V18_CURRENT_MANUAL_POSITION_LIFECYCLE_AUDIT.csv",
    "outputs/v18/ops/V18_CURRENT_FORWARD_TRACKER_READ_FIRST.txt",
    "outputs/v18/ops/V18_CURRENT_FORWARD_PRICE_FILLER_READ_FIRST.txt",
    "outputs/v18/ops/V18_CURRENT_MANUAL_FEEDBACK_READ_FIRST.txt",
]

RUNTIME_COMMANDS = [
    {
        "run_mode": "CURRENT_DEFAULT_SAFE_MODE",
        "args": [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "D:\\us-tech-quant\\scripts\\v18\\run_v18_current_daily_command_center.ps1",
        ],
    },
    {
        "run_mode": "CURRENT_FORWARD_TRACKER_AND_MANUAL_FEEDBACK",
        "args": [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "D:\\us-tech-quant\\scripts\\v18\\run_v18_current_daily_command_center.ps1",
            "-RunForwardTracker",
            "-RunManualFeedback",
        ],
    },
]

OUTPUT_SCAN_DIRS = [
    "outputs/v18/read_center",
    "outputs/v18/candidates",
    "outputs/v18/positions",
    "outputs/v18/ops",
    "state/v18",
]

FACTOR_KEYWORDS = {
    "trend": ("trend", "ma_", "sma", "ema"),
    "momentum": ("momentum", "mom", "roc", "rsi"),
    "relative_strength": ("relative_strength", "rel_strength", "rs_", "sector_rs"),
    "pullback": ("pullback", "dip", "retracement"),
    "overheat": ("overheat", "overbought", "extended"),
    "volatility": ("volatility", "atr", "rv", "stdev", "sigma"),
    "event_risk": ("event", "earnings", "risk"),
    "execution_penalty": ("execution", "penalty", "spread", "liquidity", "slippage"),
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            pass
    return ""


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
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


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def infer_version(name: str) -> str:
    m = re.search(r"(V?18[_\.]\d+[A-Z]?(?:_R\d+|[A-Z])?|v18_\d+[A-Z]?(?:_R\d+)?)", name, re.I)
    if not m:
        return ""
    return m.group(1).upper().replace(".", "_")


def is_active_chain(path: Path) -> bool:
    n = path.name.lower()
    active_bits = (
        "current_daily_command_center",
        "15b_current_daily_with_manual_feedback",
        "15a_manual_position_trade_feedback",
        "15c_predevelopment_program_audit",
        "14e_current_daily_with_forward_tracker",
        "14d_ranked_candidate_forward_price_filler",
        "14c_ranked_candidate_forward_tracker",
        "13d_daily_command_center",
        "13c_ranked_candidate_unified_link",
        "13b_ranked_candidate_read_center",
    )
    return any(bit in n for bit in active_bits)


def classify_script(path: Path) -> str:
    n = path.name.lower()
    if ".bak" in n or "before_" in n or "broken_before" in n:
        return "OBSOLETE_BACKUP"
    if is_active_chain(path):
        return "CURRENT_ACTIVE_CHAIN"
    if "stable_snapshot" in n or "_r1_" in n or "_r2_" in n or "_r3_" in n:
        return "STABLE_OR_VERSIONED_UTILITY"
    return "LEGACY_OR_ORPHAN_REVIEW"


def parse_powershell(path: Path) -> Tuple[str, str]:
    if not path.exists():
        return "MISSING", "file not found"
    ps_path = str(path.resolve()).replace("'", "''")
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f"$p='{ps_path}'; $t=$null; $e=$null; [System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$e) > $null; if ($e.Count -gt 0) {{ $e | ForEach-Object {{ $_.Message }}; exit 1 }}",
    ]
    try:
        proc = subprocess.run(command, cwd=str(path.parent), text=True, capture_output=True, timeout=60)
        if proc.returncode == 0:
            return "PASS", ""
        return "FAIL", (proc.stdout + proc.stderr).strip()[:1000]
    except Exception as exc:
        return "FAIL", f"{type(exc).__name__}: {exc}"


def compile_python(path: Path) -> Tuple[str, str]:
    if not path.exists():
        return "MISSING", "file not found"
    try:
        ast.parse(read_text(path), filename=str(path))
        return "PASS", ""
    except SyntaxError as exc:
        return "FAIL", f"{exc.msg} line {exc.lineno}"
    except Exception as exc:
        return "FAIL", f"{type(exc).__name__}: {exc}"


def script_inventory(root: Path) -> Tuple[List[Dict[str, object]], Dict[str, Tuple[str, str]], Dict[str, Tuple[str, str]]]:
    rows: List[Dict[str, object]] = []
    ps_results: Dict[str, Tuple[str, str]] = {}
    py_results: Dict[str, Tuple[str, str]] = {}
    required_ps = {str((root / p).resolve()).lower() for p in PS_PARSE_REQUIRED}
    required_py = {str((root / p).resolve()).lower() for p in PY_COMPILE_REQUIRED}
    for path in sorted((root / "scripts/v18").glob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        ps_status = ""
        py_status = ""
        note = ""
        key = str(path.resolve()).lower()
        if suffix == ".ps1" and key in required_ps:
            ps_status, note = parse_powershell(path)
            ps_results[rel(root, path)] = (ps_status, note)
        if suffix == ".py" and key in required_py:
            py_status, note = compile_python(path)
            py_results[rel(root, path)] = (py_status, note)
        stat = path.stat()
        classification = classify_script(path)
        rows.append(
            {
                "script_path": rel(root, path),
                "file_size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
                "version_tag": infer_version(path.name),
                "is_powershell_wrapper": str(suffix == ".ps1").upper(),
                "is_python_script": str(suffix == ".py").upper(),
                "belongs_to_current_active_chain": str(is_active_chain(path)).upper(),
                "organization_status": classification,
                "appears_obsolete_duplicate_or_orphaned": str(classification in {"OBSOLETE_BACKUP", "LEGACY_OR_ORPHAN_REVIEW"}).upper(),
                "parse_or_compile_status": ps_status or py_status or "NOT_CHECKED",
                "parse_or_compile_note": note,
            }
        )
    return rows, ps_results, py_results


def inventory_outputs(root: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    seen_names: Dict[str, int] = {}
    files: List[Path] = []
    for d in OUTPUT_SCAN_DIRS:
        base = root / d
        if base.exists():
            files.extend([p for p in base.rglob("*") if p.is_file()])
    for p in files:
        seen_names[p.name] = seen_names.get(p.name, 0) + 1
    now_ts = datetime.now().timestamp()
    for path in sorted(files):
        stat = path.stat()
        age_days = max(0.0, (now_ts - stat.st_mtime) / 86400.0)
        name = path.name
        is_current = "_CURRENT_" in name or name.startswith("V18_CURRENT_")
        is_versioned = bool(re.search(r"V18[_\.]\d+", name, re.I))
        rows.append(
            {
                "output_path": rel(root, path),
                "file_size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
                "is_current_alias": str(is_current).upper(),
                "is_latest_dated_or_versioned_output": str(is_versioned and age_days <= 2).upper(),
                "expected_output_status": "PRESENT",
                "duplicate_name_count": seen_names[name],
                "duplicate_output_status": "DUPLICATE_NAME" if seen_names[name] > 1 else "UNIQUE_NAME",
                "stale_output_status": "STALE_REVIEW" if age_days > 14 and not is_current else "CURRENT_OR_RECENT",
                "alias_overwrite_candidate": str(is_versioned and not is_current and seen_names[name] == 1 and stat.st_size > 0).upper(),
                "large_or_cleanup_review": "LARGE_REVIEW" if stat.st_size > 25 * 1024 * 1024 else "",
            }
        )
    expected = set(CURRENT_ALIASES)
    present = {r["output_path"] for r in rows}
    for missing in sorted(expected - present):
        rows.append(
            {
                "output_path": missing,
                "file_size": 0,
                "modified_time": "",
                "is_current_alias": "TRUE",
                "is_latest_dated_or_versioned_output": "FALSE",
                "expected_output_status": "MISSING",
                "duplicate_name_count": 0,
                "duplicate_output_status": "",
                "stale_output_status": "",
                "alias_overwrite_candidate": "FALSE",
                "large_or_cleanup_review": "",
            }
        )
    return rows


def current_alias_audit(root: Path) -> List[Dict[str, object]]:
    rows = []
    for item in CURRENT_ALIASES:
        path = root / item
        row_count = ""
        parse_status = ""
        if path.suffix.lower() == ".csv" and path.exists():
            data, _, parse_status = read_csv(path)
            row_count = len(data)
        rows.append(
            {
                "alias_path": item,
                "exists": str(path.exists()).upper(),
                "file_size": path.stat().st_size if path.exists() else 0,
                "modified_time": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds") if path.exists() else "",
                "row_count": row_count,
                "parse_status": parse_status,
                "status": "PRESENT" if path.exists() else "MISSING",
            }
        )
    return rows


def stable_snapshot_audit(root: Path) -> List[Dict[str, object]]:
    rows = []
    base = root / "archive/stable"
    if not base.exists():
        return rows
    for folder in sorted([p for p in base.iterdir() if p.is_dir()]):
        files = [p for p in folder.rglob("*") if p.is_file()]
        lower_names = [p.name.lower() for p in files]
        manifest = next((p for p in files if "manifest" in p.name.lower()), None)
        validation = next((p for p in files if "validation" in p.name.lower() or "read_first" in p.name.lower()), None)
        readme = next((p for p in files if p.name.lower().startswith("readme")), None)
        restore = next((p for p in files if "restore" in p.name.lower() and p.suffix.lower() in {".ps1", ".py", ".bat"}), None)
        missing_count = sum(x is None for x in (manifest, validation, readme, restore))
        manifest_hash_status = "NOT_AVAILABLE"
        if manifest:
            text = read_text(manifest)
            manifest_hash_status = "HASH_REFERENCES_PRESENT" if re.search(r"sha256|hash", text, re.I) else "NO_HASH_REFERENCES"
        rows.append(
            {
                "stable_snapshot_folder": rel(root, folder),
                "inferred_version": infer_version(folder.name),
                "manifest_exists": str(manifest is not None).upper(),
                "validation_file_exists": str(validation is not None).upper(),
                "readme_exists": str(readme is not None).upper(),
                "restore_script_exists": str(restore is not None).upper(),
                "manifest_hash_validation": manifest_hash_status,
                "missing_critical_file_count": missing_count,
                "protected_snapshot_modified_status": "COMPARISON_BASELINE_NOT_AVAILABLE",
                "file_count": len(files),
            }
        )
    return rows


def latest_matching(root: Path, pattern: str) -> Path | None:
    matches = [p for p in (root / "outputs/v18").rglob(pattern) if p.is_file()]
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


def score_columns(fields: Sequence[str]) -> List[str]:
    out = []
    for f in fields:
        fl = f.lower()
        if any(k in fl for k in ("score", "rank_score", "composite", "weighted", "confidence", "alpha")):
            out.append(f)
    return out


def rank_columns(fields: Sequence[str]) -> List[str]:
    return [f for f in fields if "rank" in f.lower()]


def ticker_value(row: Dict[str, str]) -> str:
    for key in ("ticker", "symbol", "Ticker", "Symbol"):
        if key in row and row.get(key):
            return str(row.get(key, "")).strip()
    for key, value in row.items():
        if key.lower() in {"ticker", "symbol"}:
            return str(value).strip()
    return ""


def numeric_values(rows: Sequence[Dict[str, str]], col: str) -> List[float]:
    vals = []
    for row in rows:
        try:
            vals.append(float(str(row.get(col, "")).replace(",", "")))
        except Exception:
            return []
    return vals


def infer_sort(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> str:
    for col in rank_columns(fields):
        vals = numeric_values(rows[: min(50, len(rows))], col)
        if vals and vals == sorted(vals):
            return f"{col} ASC"
    for col in score_columns(fields):
        vals = numeric_values(rows[: min(50, len(rows))], col)
        if vals and vals == sorted(vals, reverse=True):
            return f"{col} DESC"
    return "FILE_ORDER_OR_UNKNOWN"


def factor_columns(fields: Sequence[str]) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for factor, keys in FACTOR_KEYWORDS.items():
        cols = [f for f in fields if any(k in f.lower() for k in keys)]
        result[factor] = cols
    return result


def lineage_audit(root: Path) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    current = root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
    rows, fields, parse_status = read_csv(current)
    rank_source_status = "FOUND" if current.exists() and parse_status == "OK" else parse_status
    sort = infer_sort(rows, fields) if rows else "NO_ROWS"
    s_cols = score_columns(fields)
    f_cols = factor_columns(fields)
    missing_expected = [name for name, cols in f_cols.items() if not cols]
    scored = 0
    if s_cols:
        for row in rows:
            if any(str(row.get(c, "")).strip() not in {"", "NA", "N/A", "None"} for c in s_cols):
                scored += 1
    related = {
        "latest_v18_13b_ranked_candidate_output": latest_matching(root, "V18_13B*RANKED*CANDIDATES*.csv"),
        "latest_v18_13c_unified_ranked_output": latest_matching(root, "V18_13C*.csv"),
        "latest_v18_14b_current_daily_output": latest_matching(root, "V18_14B*.csv"),
    }
    related_text = "; ".join(f"{k}={rel(root, v) if v else 'NOT_FOUND'}" for k, v in related.items())
    script_refs = []
    for script in [
        root / "scripts/v18/v18_13B_ranked_candidate_read_center.py",
        root / "scripts/v18/v18_13C_ranked_candidate_unified_link.py",
        root / "scripts/v18/v18_14B_current_daily_command_center.py",
    ]:
        text = read_text(script).lower()
        script_refs.append(f"{rel(root, script)}:score_ref={str('score' in text).upper()},factor_ref={str('factor' in text).upper()}")
    audit_rows: List[Dict[str, object]] = []
    for factor, cols in f_cols.items():
        status = "PRESENT_BUT_NOT_VERIFIED_USED" if cols else "NOT_FOUND"
        audit_rows.append(
            {
                "audit_item": factor,
                "status": status,
                "current_ranked_candidate_source_file": rel(root, current),
                "ranking_source_status": rank_source_status,
                "sort_column_or_inferred_sort_columns": sort,
                "score_columns_present": ";".join(s_cols),
                "factor_related_columns_present": ";".join(cols),
                "missing_expected_factor_columns": ";".join(missing_expected),
                "all_ranked_candidates_have_scores": str(scored == len(rows) and len(rows) > 0).upper(),
                "ranking_appears_score_based_or_file_order": "SCORE_BASED_INFERRED" if "DESC" in sort and s_cols else "FILE_ORDER_OR_UNKNOWN",
                "current_or_stale": "CURRENT_OR_RECENT" if current.exists() else "NOT_FOUND",
                "fast_mode_prior_score_read_risk": "STALE_OR_UNKNOWN",
                "related_source_outputs": related_text,
                "source_script_references": "; ".join(script_refs),
                "note": "Usage is not marked VERIFIED_USED unless current fields and sort prove the factor participates directly.",
            }
        )
    for idx, row in enumerate(rows[:20], start=1):
        ticker = ticker_value(row)
        audit_rows.append(
            {
                "audit_item": f"TOP20_RANKED_TICKER_{idx:02d}",
                "status": "PRESENT_BUT_NOT_VERIFIED_USED" if s_cols else "NOT_VERIFIED_FROM_CURRENT_FILES",
                "current_ranked_candidate_source_file": rel(root, current),
                "ranking_source_status": rank_source_status,
                "sort_column_or_inferred_sort_columns": sort,
                "score_columns_present": ";".join(s_cols),
                "factor_related_columns_present": ";".join(f"{c}={row.get(c, '')}" for c in s_cols[:8]),
                "missing_expected_factor_columns": ";".join(missing_expected),
                "all_ranked_candidates_have_scores": str(scored == len(rows) and len(rows) > 0).upper(),
                "ranking_appears_score_based_or_file_order": "SCORE_BASED_INFERRED" if "DESC" in sort and s_cols else "FILE_ORDER_OR_UNKNOWN",
                "current_or_stale": "CURRENT_OR_RECENT" if current.exists() else "NOT_FOUND",
                "fast_mode_prior_score_read_risk": "STALE_OR_UNKNOWN",
                "related_source_outputs": related_text,
                "source_script_references": "",
                "note": ticker,
            }
        )
    top5 = [ticker_value(r) for r in rows[:5] if ticker_value(r)]
    summary = {
        "rank_source_status": rank_source_status,
        "ranked_candidate_count": len(rows),
        "scored_ticker_count": scored,
        "unscored_ticker_count": max(0, len(rows) - scored),
        "top_5_tickers": ",".join(top5),
        "score_columns": s_cols,
        "factor_columns": f_cols,
        "sort": sort,
        "factor_lineage_verified_count": sum(1 for r in audit_rows if r["status"] == "VERIFIED_USED"),
        "factor_lineage_not_verified_count": sum(1 for r in audit_rows if r["status"] != "VERIFIED_USED"),
    }
    return audit_rows, summary


def first_value_from_read_first(path: Path, key: str) -> str:
    text = read_text(path)
    target = key.upper()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        k, v = stripped.split(":", 1)
        if k.strip().upper().lstrip("- ").strip() == target:
            return v.strip()
    return ""


def count_csv_rows(path: Path) -> int:
    rows, _, status = read_csv(path)
    return len(rows) if status == "OK" else 0


def run_runtime_validations(root: Path, skip: bool) -> List[Dict[str, object]]:
    if skip:
        return [
            {
                "run_id": "SKIPPED",
                "run_mode": "SKIPPED_BY_FLAG",
                "status": "SKIPPED",
                "exit_code": "",
                "forward_tracker_status": "",
                "manual_feedback_status": "",
                "top_tickers": "",
                "tracker_rows": "",
                "pending_forward_rows": "",
                "position_count": "",
                "trade_log_rows": "",
                "validation_fail_count": 1,
                "auto_trade_status": AUTO_TRADE,
                "auto_sell_status": AUTO_SELL,
                "official_decision_impact": OFFICIAL_DECISION_IMPACT,
                "stdout_tail": "",
                "stderr_tail": "",
            }
        ]
    result_rows = []
    for idx, spec in enumerate(RUNTIME_COMMANDS, start=1):
        try:
            proc = subprocess.run(spec["args"], cwd=str(root), text=True, capture_output=True, timeout=600)
            status = "PASS" if proc.returncode == 0 else "FAIL"
            out = proc.stdout + "\n" + proc.stderr
        except Exception as exc:
            proc = None
            status = "FAIL"
            out = f"{type(exc).__name__}: {exc}"
        read_first = root / "outputs/v18/ops/V18_15B_READ_FIRST.txt"
        if not read_first.exists():
            read_first = root / "outputs/v18/ops/V18_14B_READ_FIRST.txt"
        ranked = root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
        ranked_rows, _, _ = read_csv(ranked)
        top = ",".join([ticker_value(r) for r in ranked_rows[:5] if ticker_value(r)])
        tracker_rows = count_csv_rows(root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv")
        pending_forward = 0
        tracker_data, _, tracker_status = read_csv(root / "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER.csv")
        if tracker_status == "OK":
            for row in tracker_data:
                joined = " ".join(str(v) for v in row.values()).upper()
                if "PENDING" in joined or "MISSING" in joined:
                    pending_forward += 1
        auto_trade = "DISABLED" if re.search(r"AUTO_TRADE:\s*DISABLED", out, re.I) else first_value_from_read_first(read_first, "AUTO_TRADE") or "UNKNOWN"
        auto_sell = "DISABLED" if re.search(r"AUTO_SELL:\s*DISABLED", out, re.I) else first_value_from_read_first(read_first, "AUTO_SELL") or "UNKNOWN"
        impact = "NONE" if re.search(r"OFFICIAL_DECISION_IMPACT:\s*NONE", out, re.I) else first_value_from_read_first(read_first, "OFFICIAL_DECISION_IMPACT") or "UNKNOWN"
        fail_count = 0 if status == "PASS" and auto_trade == "DISABLED" and auto_sell == "DISABLED" and impact == "NONE" else 1
        result_rows.append(
            {
                "run_id": idx,
                "run_mode": spec["run_mode"],
                "status": status,
                "exit_code": proc.returncode if proc else "",
                "forward_tracker_status": "RAN" if "-RunForwardTracker" in spec["args"] else "SKIPPED",
                "manual_feedback_status": "RAN" if "-RunManualFeedback" in spec["args"] else "SKIPPED",
                "top_tickers": top,
                "tracker_rows": tracker_rows,
                "pending_forward_rows": pending_forward,
                "position_count": count_csv_rows(root / "outputs/v18/positions/V18_CURRENT_MANUAL_POSITION_REVIEW.csv"),
                "trade_log_rows": count_csv_rows(root / "outputs/v18/positions/V18_CURRENT_MANUAL_TRADE_FEEDBACK.csv"),
                "validation_fail_count": fail_count,
                "auto_trade_status": auto_trade,
                "auto_sell_status": auto_sell,
                "official_decision_impact": impact,
                "stdout_tail": "\n".join(proc.stdout.splitlines()[-20:]) if proc else "",
                "stderr_tail": "\n".join(proc.stderr.splitlines()[-20:]) if proc else out,
            }
        )
    return result_rows


def dangerous_token_scan(root: Path, new_outputs: Sequence[Path]) -> List[Dict[str, object]]:
    token_parts = [
        ("BUY", "NOW"),
        ("SELL", "NOW"),
        ("EXECUTE", "LIVE_ORDER"),
        ("LIVE", "TRADE"),
        ("LIVE", "SELL"),
    ]
    exact_tokens = ["_".join(p) for p in token_parts]
    guarded_patterns = [("AUTO_TRADE", "ENABLED"), ("AUTO_SELL", "ENABLED")]
    paths = list(new_outputs)
    for item in [
        "scripts/v18/run_v18_current_daily_command_center.ps1",
        "scripts/v18/run_v18_15B_current_daily_with_manual_feedback.ps1",
        "scripts/v18/run_v18_15A_manual_position_trade_feedback.ps1",
        "scripts/v18/run_v18_14E_current_daily_with_forward_tracker.ps1",
        "scripts/v18/run_v18_14C_ranked_candidate_forward_tracker.ps1",
        "scripts/v18/run_v18_14D_ranked_candidate_forward_price_filler.ps1",
    ]:
        paths.append(root / item)
    rows = []
    for path in paths:
        text = read_text(path)
        if not text:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            upper = line.upper()
            safe_disabled = "DISABLED" in upper or "DO NOT" in upper or "DANGEROUS" in upper
            for token in exact_tokens:
                if token in upper and not safe_disabled:
                    rows.append({"file_path": rel(root, path), "line_number": line_no, "token": token, "context": line.strip()[:240], "finding_status": "FINDING"})
            for key, value in guarded_patterns:
                if key in upper and value in upper:
                    rows.append({"file_path": rel(root, path), "line_number": line_no, "token": f"{key}: {value}", "context": line.strip()[:240], "finding_status": "FINDING"})
    return rows


def recommendations(
    ps_fail: int,
    py_fail: int,
    runtime_fail: int,
    dangerous_count: int,
    stable_fail: int,
    alias_missing: int,
    lineage_summary: Dict[str, object],
    inventory_rows: Sequence[Dict[str, object]],
) -> List[Dict[str, object]]:
    rows = []

    def add(sev: str, cat: str, finding: str, rec: str, fix: bool, version: str) -> None:
        rows.append(
            {
                "recommendation_id": f"V18_15C_REC_{len(rows)+1:03d}",
                "severity": sev,
                "category": cat,
                "finding": finding,
                "recommendation": rec,
                "should_fix_before_v18_16": str(fix).upper(),
                "suggested_next_version": version,
            }
        )

    if ps_fail:
        add("BLOCKER", "SCRIPT_ORGANIZATION", f"{ps_fail} PowerShell parse checks failed.", "Fix parse failures before V18.16 development.", True, "V18.15C-R1")
    if py_fail:
        add("BLOCKER", "SCRIPT_ORGANIZATION", f"{py_fail} Python compile checks failed.", "Fix compile failures before V18.16 development.", True, "V18.15C-R1")
    if runtime_fail:
        add("BLOCKER", "RUNTIME_VALIDATION", f"{runtime_fail} safe runtime validation runs failed.", "Resolve safe current daily validation failures before V18.16.", True, "V18.15C-R1")
    if dangerous_count:
        add("BLOCKER", "SAFETY_GUARD", f"{dangerous_count} dangerous token findings found.", "Remove or quarantine unsafe execution language before V18.16.", True, "V18.15C-R1")
    if stable_fail:
        add("BLOCKER", "STABLE_SNAPSHOT", f"{stable_fail} stable snapshots have missing critical files.", "Review latest stable snapshot completeness before V18.16.", True, "V18.15C-R1")
    if lineage_summary.get("rank_source_status") != "FOUND":
        add("BLOCKER", "RANKING_LINEAGE", "Current ranked candidate source was not found.", "Restore or regenerate current ranked candidates before rolling universe scan work.", True, "V18.15C-R1")
    if lineage_summary.get("factor_lineage_verified_count", 0) == 0:
        add("HIGH", "RANKING_LINEAGE", "No current ranking factors were verified as directly used from current files.", "Before V18.16, document or expose ranking score construction fields so factor usage is auditable.", True, "V18.16")
    if alias_missing:
        add("MEDIUM", "CURRENT_ALIAS", f"{alias_missing} expected current aliases are missing.", "Create missing aliases through the existing daily chain, not by manual rewrite.", False, "V18.16")
    stale_count = sum(1 for r in inventory_rows if r.get("stale_output_status") == "STALE_REVIEW")
    if stale_count:
        add("LOW", "OUTPUT_RETENTION", f"{stale_count} scanned outputs are stale retention review candidates.", "Plan a non-destructive retention policy after V18.16 design is complete.", False, "V18.16")
    add("MEDIUM", "PERFORMANCE_PREP", "Rolling universe scan will likely increase generated outputs and repeated alias writes.", "Define alias-overwrite and dated-output retention rules before broad universe runs.", True, "V18.16")
    return rows


def markdown_report(summary: Dict[str, object], lineage_summary: Dict[str, object], recs: Sequence[Dict[str, object]]) -> str:
    lines = [
        "# V18.15C Current Pre-Development Program Audit Report",
        "",
        f"Generated: {now_iso()}",
        "",
        "## Summary",
    ]
    for key in [
        "STATUS",
        "READY_FOR_V18_16",
        "VALIDATION_FAIL_COUNT",
        "RANK_SOURCE_STATUS",
        "RANKED_CANDIDATE_COUNT",
        "SCORED_TICKER_COUNT",
        "UNSCORED_TICKER_COUNT",
        "TOP_5_TICKERS",
        "AUTO_TRADE",
        "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT",
    ]:
        lines.append(f"- {key}: {summary.get(key, '')}")
    lines.extend(
        [
            "",
            "## Ranking Lineage",
            f"- Current source: outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv",
            f"- Ranking source status: {lineage_summary.get('rank_source_status')}",
            f"- Inferred sort: {lineage_summary.get('sort')}",
            f"- Score columns: {', '.join(lineage_summary.get('score_columns', [])) or 'NOT_FOUND'}",
            "- Factor usage is reported conservatively; factors are not marked VERIFIED_USED unless current files prove direct ranking use.",
            "",
            "## Recommendations",
        ]
    )
    for rec in recs:
        lines.append(f"- {rec['severity']} {rec['category']}: {rec['finding']} Recommendation: {rec['recommendation']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:\\us-tech-quant")
    parser.add_argument("--skip-runtime-validation", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ops = root / "outputs/v18/ops"
    ensure_dir(ops)

    script_rows, ps_results, py_results = script_inventory(root)
    output_rows = inventory_outputs(root)
    alias_rows = current_alias_audit(root)
    stable_rows = stable_snapshot_audit(root)
    lineage_rows, lineage_summary = lineage_audit(root)
    runtime_rows = run_runtime_validations(root, args.skip_runtime_validation)

    paths = {
        "read_first": ops / "V18_15C_READ_FIRST.txt",
        "report": ops / "V18_15C_CURRENT_PREDEVELOPMENT_PROGRAM_AUDIT_REPORT.md",
        "script_inventory": ops / "V18_15C_CURRENT_SCRIPT_INVENTORY.csv",
        "output_inventory": ops / "V18_15C_CURRENT_OUTPUT_INVENTORY.csv",
        "stable": ops / "V18_15C_CURRENT_STABLE_SNAPSHOT_AUDIT.csv",
        "alias": ops / "V18_15C_CURRENT_CURRENT_ALIAS_AUDIT.csv",
        "lineage": ops / "V18_15C_CURRENT_RANKING_FACTOR_LINEAGE_AUDIT.csv",
        "runtime": ops / "V18_15C_CURRENT_RUNTIME_VALIDATION_AUDIT.csv",
        "danger": ops / "V18_15C_CURRENT_DANGEROUS_TOKEN_SCAN.csv",
        "recs": ops / "V18_15C_CURRENT_PREDEVELOPMENT_RECOMMENDATIONS.csv",
        "alias_report": ops / "V18_CURRENT_PREDEVELOPMENT_PROGRAM_AUDIT_REPORT.md",
        "alias_lineage": ops / "V18_CURRENT_RANKING_FACTOR_LINEAGE_AUDIT.csv",
        "alias_read": ops / "V18_CURRENT_PREDEVELOPMENT_AUDIT_READ_FIRST.txt",
    }

    write_csv(
        paths["script_inventory"],
        script_rows,
        [
            "script_path",
            "file_size",
            "modified_time",
            "version_tag",
            "is_powershell_wrapper",
            "is_python_script",
            "belongs_to_current_active_chain",
            "organization_status",
            "appears_obsolete_duplicate_or_orphaned",
            "parse_or_compile_status",
            "parse_or_compile_note",
        ],
    )
    write_csv(
        paths["output_inventory"],
        output_rows,
        [
            "output_path",
            "file_size",
            "modified_time",
            "is_current_alias",
            "is_latest_dated_or_versioned_output",
            "expected_output_status",
            "duplicate_name_count",
            "duplicate_output_status",
            "stale_output_status",
            "alias_overwrite_candidate",
            "large_or_cleanup_review",
        ],
    )
    write_csv(paths["stable"], stable_rows, ["stable_snapshot_folder", "inferred_version", "manifest_exists", "validation_file_exists", "readme_exists", "restore_script_exists", "manifest_hash_validation", "missing_critical_file_count", "protected_snapshot_modified_status", "file_count"])
    write_csv(paths["alias"], alias_rows, ["alias_path", "exists", "file_size", "modified_time", "row_count", "parse_status", "status"])
    write_csv(paths["lineage"], lineage_rows, ["audit_item", "status", "current_ranked_candidate_source_file", "ranking_source_status", "sort_column_or_inferred_sort_columns", "score_columns_present", "factor_related_columns_present", "missing_expected_factor_columns", "all_ranked_candidates_have_scores", "ranking_appears_score_based_or_file_order", "current_or_stale", "fast_mode_prior_score_read_risk", "related_source_outputs", "source_script_references", "note"])
    write_csv(paths["runtime"], runtime_rows, ["run_id", "run_mode", "status", "exit_code", "forward_tracker_status", "manual_feedback_status", "top_tickers", "tracker_rows", "pending_forward_rows", "position_count", "trade_log_rows", "validation_fail_count", "auto_trade_status", "auto_sell_status", "official_decision_impact", "stdout_tail", "stderr_tail"])

    danger_rows = dangerous_token_scan(root, [p for p in paths.values() if p.exists() and p.name.startswith("V18_15C")])
    write_csv(paths["danger"], danger_rows, ["file_path", "line_number", "token", "context", "finding_status"])

    ps_fail = sum(1 for status, _ in ps_results.values() if status != "PASS")
    py_fail = sum(1 for status, _ in py_results.values() if status != "PASS")
    ps_pass = sum(1 for status, _ in ps_results.values() if status == "PASS")
    py_pass = sum(1 for status, _ in py_results.values() if status == "PASS")
    runtime_fail = sum(1 for r in runtime_rows if str(r.get("status")) != "PASS" or int(r.get("validation_fail_count") or 0) > 0)
    alias_missing = sum(1 for r in alias_rows if r["status"] == "MISSING")
    stable_fail = sum(1 for r in stable_rows if int(r.get("missing_critical_file_count") or 0) > 0 and str(r.get("inferred_version", "")).startswith("V18_15"))
    dangerous_count = len(danger_rows)
    validation_fail_count = ps_fail + py_fail + runtime_fail + dangerous_count + stable_fail

    recs = recommendations(ps_fail, py_fail, runtime_fail, dangerous_count, stable_fail, alias_missing, lineage_summary, output_rows)
    blocker_count = sum(1 for r in recs if r["severity"] == "BLOCKER")
    write_csv(paths["recs"], recs, ["recommendation_id", "severity", "category", "finding", "recommendation", "should_fix_before_v18_16", "suggested_next_version"])

    ready = (
        ps_fail == 0
        and py_fail == 0
        and runtime_fail == 0
        and dangerous_count == 0
        and stable_fail == 0
        and lineage_summary.get("rank_source_status") == "FOUND"
        and AUTO_TRADE == "DISABLED"
        and AUTO_SELL == "DISABLED"
        and OFFICIAL_DECISION_IMPACT == "NONE"
    )
    status = STATUS_OK if ready else STATUS_WARN
    summary = {
        "STATUS": status,
        "MODE": MODE,
        "SCRIPT_COUNT": len(script_rows),
        "POWERSHELL_PARSE_PASS_COUNT": ps_pass,
        "POWERSHELL_PARSE_FAIL_COUNT": ps_fail,
        "PYTHON_COMPILE_PASS_COUNT": py_pass,
        "PYTHON_COMPILE_FAIL_COUNT": py_fail,
        "CURRENT_ALIAS_CHECK_COUNT": len(alias_rows),
        "CURRENT_ALIAS_MISSING_COUNT": alias_missing,
        "STABLE_SNAPSHOT_COUNT": len(stable_rows),
        "STABLE_SNAPSHOT_FAIL_COUNT": stable_fail,
        "RUNTIME_VALIDATION_RUN_COUNT": len([r for r in runtime_rows if r.get("status") != "SKIPPED"]),
        "RUNTIME_VALIDATION_FAIL_COUNT": runtime_fail,
        "RANK_SOURCE_STATUS": lineage_summary.get("rank_source_status"),
        "RANKED_CANDIDATE_COUNT": lineage_summary.get("ranked_candidate_count"),
        "SCORED_TICKER_COUNT": lineage_summary.get("scored_ticker_count"),
        "UNSCORED_TICKER_COUNT": lineage_summary.get("unscored_ticker_count"),
        "TOP_5_TICKERS": lineage_summary.get("top_5_tickers"),
        "FACTOR_LINEAGE_VERIFIED_COUNT": lineage_summary.get("factor_lineage_verified_count"),
        "FACTOR_LINEAGE_NOT_VERIFIED_COUNT": lineage_summary.get("factor_lineage_not_verified_count"),
        "DANGEROUS_TOKEN_FINDING_COUNT": dangerous_count,
        "RECOMMENDATION_COUNT": len(recs),
        "BLOCKER_RECOMMENDATION_COUNT": blocker_count,
        "READY_FOR_V18_16": str(ready).upper(),
        "VALIDATION_FAIL_COUNT": validation_fail_count,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }

    read_first = "\n".join(f"{k}: {v}" for k, v in summary.items()) + "\n"
    write_text(paths["read_first"], read_first)
    report = markdown_report(summary, lineage_summary, recs)
    write_text(paths["report"], report)
    write_text(paths["alias_read"], read_first)
    write_text(paths["alias_report"], report)
    write_csv(paths["alias_lineage"], lineage_rows, ["audit_item", "status", "current_ranked_candidate_source_file", "ranking_source_status", "sort_column_or_inferred_sort_columns", "score_columns_present", "factor_related_columns_present", "missing_expected_factor_columns", "all_ranked_candidates_have_scores", "ranking_appears_score_based_or_file_order", "current_or_stale", "fast_mode_prior_score_read_risk", "related_source_outputs", "source_script_references", "note"])

    for key in [
        "STATUS",
        "READY_FOR_V18_16",
        "VALIDATION_FAIL_COUNT",
        "BLOCKER_RECOMMENDATION_COUNT",
        "RANK_SOURCE_STATUS",
        "TOP_5_TICKERS",
        "AUTO_TRADE",
        "AUTO_SELL",
        "OFFICIAL_DECISION_IMPACT",
    ]:
        print(f"{key}: {summary[key]}")
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
