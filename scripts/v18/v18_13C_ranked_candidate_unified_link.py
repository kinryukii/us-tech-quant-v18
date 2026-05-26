from __future__ import annotations

import argparse
import csv
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


ROOT_DEFAULT = Path(r"D:\us-tech-quant")

STATUS_OK = "OK_V18_13C_UNIFIED_DAILY_WITH_RANKED_CANDIDATES_READY"
STATUS_WARN_B_MISSING = "WARN_V18_13C_RANKED_CANDIDATES_MISSING"
STATUS_FAIL_A_MISSING = "FAIL_V18_13C_UNIFIED_DAILY_MISSING"
STATUS_FAIL_DANGEROUS = "FAIL_V18_13C_DANGEROUS_TOKEN_FOUND"

LINK_STATUS_OK = "OK_LINKED_V18_13A_AND_V18_13B"
LINK_STATUS_B_MISSING = "MISSING_V18_13B_RANKED_CANDIDATES"

OFFICIAL_DECISION_IMPACT = "NONE"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
READ_ONLY = "TRUE"
LINK_ONLY = "TRUE"

DANGEROUS_TOKENS = (
    "BUY_NOW",
    "SELL_NOW",
    "EXECUTE_ORDER",
    "PLACE_ORDER",
    "AUTO_TRADE: ENABLED",
    "AUTO_SELL: ENABLED",
)

A_INPUTS = {
    "V18_13A_READ_FIRST": "outputs/v18/read_center/V18_13A_READ_FIRST.txt",
    "V18_13A_READ_CENTER": "outputs/v18/read_center/V18_13A_CURRENT_UNIFIED_DAILY_READ_CENTER.md",
    "V18_13A_SUMMARY": "outputs/v18/read_center/V18_13A_CURRENT_UNIFIED_DAILY_SUMMARY.csv",
    "V18_13A_INPUT_AUDIT": "outputs/v18/read_center/V18_13A_CURRENT_UNIFIED_DAILY_INPUT_AUDIT.csv",
}

B_INPUTS = {
    "V18_13B_READ_FIRST": "outputs/v18/read_center/V18_13B_READ_FIRST.txt",
    "V18_13B_READ_CENTER": "outputs/v18/read_center/V18_13B_CURRENT_RANKED_CANDIDATE_READ_CENTER.md",
    "V18_13B_CANDIDATES": "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES.csv",
    "V18_13B_INPUT_AUDIT": "outputs/v18/candidates/V18_13B_CURRENT_RANKED_CANDIDATES_INPUT_AUDIT.csv",
    "V18_13B_SUMMARY": "outputs/v18/read_center/V18_13B_CURRENT_RANKED_CANDIDATE_SUMMARY.csv",
}

SUMMARY_FIELDS = ["metric", "value"]
AUDIT_FIELDS = [
    "component",
    "source_file",
    "exists",
    "row_count",
    "parse_status",
    "status_value",
    "note",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    if not path.exists():
        return [], [], "MISSING"
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or []), "OK"
        except Exception:
            continue
    return [], [], "CSV_PARSE_FAILED"


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def rel_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def first_value(text: str, key: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    target = key if key.endswith(":") else f"{key}:"
    bullet_target = f"- {target}"
    for i, line in enumerate(lines):
        if line == target:
            for nxt in lines[i + 1 :]:
                if nxt:
                    return nxt.strip("` ")
        if line.startswith(target):
            value = line[len(target) :].strip()
            if value:
                return value.strip("` ")
        if line.startswith(bullet_target):
            value = line[len(bullet_target) :].strip()
            if value:
                return value.strip("` ")
    return ""


def summary_map(rows: Sequence[Dict[str, str]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for row in rows:
        metric = row.get("metric", "").strip()
        if metric:
            out[metric] = row.get("value", "").strip()
    return out


def audit_row(component: str, path: Path, row_count: int, parse_status: str, status_value: str, note: str) -> Dict[str, str]:
    return {
        "component": component,
        "source_file": str(path),
        "exists": "YES" if path.exists() else "NO",
        "row_count": str(row_count),
        "parse_status": parse_status,
        "status_value": status_value,
        "note": note,
    }


def markdown_table(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> List[str]:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        values = [str(row.get(field, "")).replace("|", "/") for field in fields]
        out.append("| " + " | ".join(values) + " |")
    return out


def build_audit(root: Path) -> Tuple[List[Dict[str, str]], Dict[str, Tuple[List[Dict[str, str]], List[str], str]]]:
    parsed: Dict[str, Tuple[List[Dict[str, str]], List[str], str]] = {}
    audit: List[Dict[str, str]] = []
    for component, rel in {**A_INPUTS, **B_INPUTS}.items():
        path = root / rel
        rows: List[Dict[str, str]] = []
        fields: List[str] = []
        parse_status = "OK_TEXT" if path.exists() else "MISSING"
        status_value = "MISSING"
        if path.suffix.lower() == ".csv":
            rows, fields, parse_status = read_csv(path)
            parsed[component] = (rows, fields, parse_status)
            if component.endswith("SUMMARY"):
                status_value = summary_map(rows).get("STATUS", "MISSING" if not path.exists() else "")
        elif path.exists():
            text = read_text(path)
            status_value = first_value(text, "STATUS") or ""
        audit.append(audit_row(component, path, len(rows), parse_status, status_value, "REQUIRED_INPUT"))
    guardrails = {
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "READ_ONLY": READ_ONLY,
        "LINK_ONLY": LINK_ONLY,
    }
    for component, value in guardrails.items():
        audit.append(
            {
                "component": component,
                "source_file": "V18.13C",
                "exists": "YES",
                "row_count": "0",
                "parse_status": "OK_GUARDRAIL",
                "status_value": value,
                "note": "OUTPUT_GUARDRAIL",
            }
        )
    return audit, parsed


def extract_source_dedup(v18_13b_summary: Dict[str, str], v18_13b_text: str) -> List[str]:
    primary = v18_13b_summary.get("PRIMARY_SCORE_SOURCE_FILES", "")
    audit_only = v18_13b_summary.get("AUDIT_ONLY_SOURCE_FILES", "")
    policy = v18_13b_summary.get("RANKING_SOURCE_POLICY", "")
    fallback = first_value(v18_13b_text, "fallback_used") or "UNKNOWN"
    lines = [
        f"- primary_files_used_for_ranking: {primary or 'UNKNOWN'}",
        f"- audit_only_files_excluded_from_ranking: {audit_only or 'UNKNOWN'}",
        f"- fallback_used: {fallback}",
        f"- ranking_source_policy: {policy or 'UNKNOWN'}",
    ]
    return lines


def dangerous_token_hits(paths: Sequence[Path]) -> List[str]:
    hits: List[str] = []
    for path in paths:
        text = read_text(path)
        for token in DANGEROUS_TOKENS:
            if token in text:
                hits.append(f"{path}:{token}")
    return hits


def make_read_center(
    status: str,
    link_status: str,
    a_status: str,
    b_status: str,
    b_summary: Dict[str, str],
    a_summary_rows: Sequence[Dict[str, str]],
    candidate_rows: Sequence[Dict[str, str]],
    v18_13b_text: str,
) -> str:
    top_fields = ["rank", "ticker", "composite_candidate_score", "final_action", "technical_status", "latest_price_date", "latest_close"]
    a_fields = ["section", "metric", "value", "status"]
    lines = [
        "# V18.13C Unified Daily With Ranked Candidates",
        "",
        f"STATUS: {status}",
        f"LINK_STATUS: {link_status}",
        f"V18_13A_STATUS: {a_status}",
        f"V18_13B_STATUS: {b_status}",
        f"RANK_SOURCE_STATUS: {b_summary.get('RANK_SOURCE_STATUS', 'MISSING')}",
        f"SECOND_STAGE_COUNT: {b_summary.get('SECOND_STAGE_COUNT', '0')}",
        f"SCORED_TICKER_COUNT: {b_summary.get('SCORED_TICKER_COUNT', '0')}",
        f"UNSCORED_TICKER_COUNT: {b_summary.get('UNSCORED_TICKER_COUNT', '0')}",
        f"TOP_5_TICKERS: {b_summary.get('TOP_5_TICKERS', '')}",
        f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
        f"AUTO_TRADE: {AUTO_TRADE}",
        f"AUTO_SELL: {AUTO_SELL}",
        f"READ_ONLY: {READ_ONLY}",
        f"LINK_ONLY: {LINK_ONLY}",
        "",
        "## TOP_RANKED_CANDIDATES",
    ]
    if candidate_rows:
        lines.extend(markdown_table(candidate_rows[:20], top_fields))
    else:
        lines.append("No V18.13B ranked candidate rows are available.")
    lines.extend(
        [
            "",
            "## V18.13A Unified Daily Status Summary",
        ]
    )
    if a_summary_rows:
        lines.extend(markdown_table(a_summary_rows, a_fields))
    else:
        lines.append("No V18.13A summary rows are available.")
    lines.extend(
        [
            "",
            "## SOURCE_DEDUP_POLICY",
            *extract_source_dedup(b_summary, v18_13b_text),
            "",
            "## LIMITATIONS",
            "- Ranked candidates are surfaced as research priority only.",
            "- V18.13C does not convert ranked candidates into official decisions or trading instructions.",
            "- This link reads existing local outputs only and does not call network data providers.",
            "- Missing ranked candidate inputs produce a warning link status, not an official decision change.",
        ]
    )
    return "\n".join(lines) + "\n"


def make_read_first(result: Dict[str, str]) -> str:
    keys = [
        "STATUS",
        "LINK_STATUS",
        "V18_13A_STATUS",
        "V18_13B_STATUS",
        "RANK_SOURCE_STATUS",
        "SECOND_STAGE_COUNT",
        "SCORED_TICKER_COUNT",
        "UNSCORED_TICKER_COUNT",
        "TOP_5_TICKERS",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "READ_ONLY",
        "LINK_ONLY",
        "READ_CENTER",
        "SUMMARY_CSV",
        "INPUT_AUDIT",
    ]
    return "\n".join([f"{key}: {result.get(key, '')}" for key in keys]) + "\n"


def run(root: Path) -> Dict[str, str]:
    read_center_dir = root / "outputs/v18/read_center"
    read_center_md = read_center_dir / "V18_13C_CURRENT_UNIFIED_DAILY_WITH_RANKED_CANDIDATES.md"
    read_first_txt = read_center_dir / "V18_13C_READ_FIRST.txt"
    summary_csv = read_center_dir / "V18_13C_CURRENT_UNIFIED_DAILY_WITH_RANKED_CANDIDATES_SUMMARY.csv"
    audit_csv = read_center_dir / "V18_13C_CURRENT_UNIFIED_DAILY_WITH_RANKED_CANDIDATES_INPUT_AUDIT.csv"

    audit_rows, parsed = build_audit(root)
    a_missing = [root / rel for rel in A_INPUTS.values() if not (root / rel).exists()]
    b_missing = [root / rel for rel in B_INPUTS.values() if not (root / rel).exists()]

    a_summary_rows, _, _ = parsed.get("V18_13A_SUMMARY", ([], [], "MISSING"))
    b_summary_rows, _, _ = parsed.get("V18_13B_SUMMARY", ([], [], "MISSING"))
    candidate_rows, _, _ = parsed.get("V18_13B_CANDIDATES", ([], [], "MISSING"))
    a_summary = summary_map(a_summary_rows)
    b_summary = summary_map(b_summary_rows)

    a_text = read_text(root / A_INPUTS["V18_13A_READ_FIRST"])
    b_text = read_text(root / B_INPUTS["V18_13B_READ_CENTER"])
    a_status = a_summary.get("STATUS") or first_value(a_text, "STATUS") or ("MISSING" if a_missing else "")
    b_status = b_summary.get("STATUS") or first_value(read_text(root / B_INPUTS["V18_13B_READ_FIRST"]), "STATUS") or ("MISSING" if b_missing else "")

    if a_missing:
        status = STATUS_FAIL_A_MISSING
        link_status = "MISSING_V18_13A_UNIFIED_DAILY"
    elif b_missing:
        status = STATUS_WARN_B_MISSING
        link_status = LINK_STATUS_B_MISSING
        b_status = "MISSING"
    else:
        status = STATUS_OK
        link_status = LINK_STATUS_OK

    result = {
        "STATUS": status,
        "LINK_STATUS": link_status,
        "V18_13A_STATUS": a_status,
        "V18_13B_STATUS": b_status,
        "RANK_SOURCE_STATUS": b_summary.get("RANK_SOURCE_STATUS", "MISSING" if b_missing else ""),
        "SECOND_STAGE_COUNT": b_summary.get("SECOND_STAGE_COUNT", "0"),
        "SCORED_TICKER_COUNT": b_summary.get("SCORED_TICKER_COUNT", "0"),
        "UNSCORED_TICKER_COUNT": b_summary.get("UNSCORED_TICKER_COUNT", "0"),
        "TOP_5_TICKERS": b_summary.get("TOP_5_TICKERS", ""),
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "READ_ONLY": READ_ONLY,
        "LINK_ONLY": LINK_ONLY,
        "READ_FIRST": rel_path(root, read_first_txt),
        "READ_CENTER": rel_path(root, read_center_md),
        "SUMMARY_CSV": rel_path(root, summary_csv),
        "INPUT_AUDIT": rel_path(root, audit_csv),
    }

    summary_rows = [{"metric": key, "value": value} for key, value in result.items()]
    write_text(read_center_md, make_read_center(status, link_status, a_status, b_status, b_summary, a_summary_rows, candidate_rows, b_text))
    write_text(read_first_txt, make_read_first(result))
    write_csv(summary_csv, summary_rows, SUMMARY_FIELDS)
    write_csv(audit_csv, audit_rows, AUDIT_FIELDS)

    output_paths = [read_center_md, read_first_txt, summary_csv, audit_csv]
    hits = dangerous_token_hits(output_paths)
    if hits:
        result["STATUS"] = STATUS_FAIL_DANGEROUS
        fail_rows = [{"metric": key, "value": value} for key, value in result.items()]
        fail_text = make_read_first(result) + "ERROR: dangerous token found in generated V18.13C outputs\n"
        write_text(read_first_txt, fail_text)
        write_csv(summary_csv, fail_rows, SUMMARY_FIELDS)
        raise RuntimeError(STATUS_FAIL_DANGEROUS)

    for key in (
        "STATUS",
        "V18_13A_STATUS",
        "V18_13B_STATUS",
        "RANK_SOURCE_STATUS",
        "SECOND_STAGE_COUNT",
        "SCORED_TICKER_COUNT",
        "UNSCORED_TICKER_COUNT",
        "TOP_5_TICKERS",
        "OFFICIAL_DECISION_IMPACT",
        "AUTO_TRADE",
        "AUTO_SELL",
        "READ_ONLY",
        "LINK_ONLY",
        "READ_FIRST",
        "READ_CENTER",
    ):
        print(f"{key}: {result.get(key, '')}")

    if status == STATUS_FAIL_A_MISSING:
        raise RuntimeError(STATUS_FAIL_A_MISSING)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.13C ranked candidate unified daily link")
    parser.add_argument("--root", default=str(ROOT_DEFAULT))
    args = parser.parse_args()
    try:
        run(Path(args.root))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
