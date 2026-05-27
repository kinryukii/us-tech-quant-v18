# -*- coding: utf-8 -*-
"""
V18.3D-R1 official review overlap fix.

Purpose:
- Keep V18.3D factor-pack shadow results unchanged.
- Repair official-review source detection.
- Recompute shadow top30 vs official review / locked candidates overlap.
- Never change V17 official BUY/NO_BUY decisions.
"""

from __future__ import annotations

import csv
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


VERSION = "V18.3D-R1"
STATUS_OK = "OK_OFFICIAL_OVERLAP_FIXED"
STATUS_WARN = "WARN_OFFICIAL_REVIEW_SOURCE_FALLBACK_USED"
STATUS_FAIL = "FAIL_OFFICIAL_OVERLAP_FIX"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def root_dir() -> Path:
    env = os.environ.get("US_TECH_QUANT_ROOT", "").strip()
    if env:
        return Path(env)
    # script is expected at D:\us-tech-quant\scripts\v18\*.py
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize_ticker(x: str) -> str:
    return str(x).strip().upper().replace("　", "")


def find_ticker_column(fieldnames: Sequence[str]) -> Optional[str]:
    lowered = [(c, c.lower().strip()) for c in fieldnames]
    exact_priority = ("ticker", "symbol", "name")
    for target in exact_priority:
        for original, low in lowered:
            if low == target:
                return original
    for original, low in lowered:
        if "ticker" in low or "symbol" in low:
            return original
    return None


def read_csv_dicts(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    for enc in ("utf-8-sig", "utf-8", "cp932", "gbk"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                return rows, list(reader.fieldnames or [])
        except Exception:
            continue
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return rows, list(reader.fieldnames or [])


def load_ranking(root: Path) -> Tuple[List[Dict[str, str]], List[str], str]:
    ranking = root / "outputs" / "v18" / "factor_pack" / "V18_3D_RAW105_FACTOR_PACK_RANKING.csv"
    if not ranking.exists():
        raise FileNotFoundError(f"ranking csv not found: {ranking}")

    rows, fields = read_csv_dicts(ranking)
    ticker_col = find_ticker_column(fields)
    if not ticker_col:
        raise RuntimeError(f"ticker column not found in ranking csv: {ranking}")

    clean_rows: List[Dict[str, str]] = []
    tickers: List[str] = []
    for row in rows:
        t = normalize_ticker(row.get(ticker_col, ""))
        if not t:
            continue
        row = dict(row)
        row["_ticker"] = t
        clean_rows.append(row)
        tickers.append(t)
    return clean_rows, tickers, str(ranking)


def tickers_from_fragment(fragment: str, universe: Set[str]) -> List[str]:
    if not fragment:
        return []
    # Split on normal separators, but keep dot tickers if any.
    raw = re.findall(r"\b[A-Z][A-Z0-9.\-]{0,7}\b", fragment.upper())
    bad = {
        "NONE", "COUNT", "NAMES", "NAME", "TICKERS", "TICKER", "TOP", "TOP30",
        "AND", "ONLY", "NOT", "SHADOW", "OFFICIAL", "REVIEW", "SOURCE",
        "LOCKED", "FALLBACK", "STRICT", "CONFIRMED", "CSV", "MD", "TXT",
        "OK", "FAIL", "WARN", "RAW", "RAW105", "PRICE", "STATUS", "TRUE",
        "FALSE", "NO", "YES", "TODAY", "EVENT", "BUDGET", "BUY", "SELL",
    }
    out: List[str] = []
    for token in raw:
        token = normalize_ticker(token)
        if token in bad:
            continue
        if token in universe and token not in out:
            out.append(token)
    return out


def extract_from_text(path: Path, universe: Set[str]) -> List[str]:
    text = read_text(path)
    found: List[str] = []

    for line in text.splitlines():
        original = line.strip()
        if not original:
            continue
        upper = original.upper()

        # Avoid pure count / status lines with no names.
        if "COUNT" in upper and "NAMES" not in upper and "TICKERS" not in upper:
            continue
        if "SHADOW_TOP30_ONLY" in upper:
            continue

        # Explicit official/review list lines. Include "AND_OFFICIAL_REVIEW" and
        # "OFFICIAL_REVIEW_NOT_SHADOW" because together they can reconstruct official review.
        is_relevant = False
        relevant_keys = [
            "WORTH_REVIEW_BUT_LOCKED",
            "WORTH-REVIEW-BUT-LOCKED",
            "WORTH REVIEW BUT LOCKED",
            "OFFICIAL_REVIEW",
            "OFFICIAL REVIEW",
            "REVIEW_LOCKED",
            "REVIEW LOCKED",
            "LOCKED_CANDIDATE",
            "LOCKED CANDIDATE",
        ]
        if any(k in upper for k in relevant_keys):
            is_relevant = True

        # Markdown / CSV-like table rows where a row itself is tagged.
        if ("REVIEW" in upper and "LOCK" in upper) or ("WORTH" in upper and "REVIEW" in upper):
            is_relevant = True

        if not is_relevant:
            continue

        # Skip lines that are clearly source/status but contain no list.
        if "SOURCE:" in upper and not any(t in upper for t in universe):
            continue

        names = tickers_from_fragment(original, universe)
        for t in names:
            if t not in found:
                found.append(t)

    return found


def score_candidate_source(path: Path, names: List[str]) -> int:
    count = len(names)
    p = str(path).upper()
    score = 0

    # Counts near the expected official review/locked candidate size are best.
    if 8 <= count <= 20:
        score += 100
    elif 5 <= count <= 40:
        score += 70
    elif 1 <= count <= 4:
        score += 10

    if "V18_3B_R2" in p or "STRICT" in p or "FACTOR_SHADOW" in p:
        score += 25
    if "V17_8D" in p:
        score += 20
    if "V17_8C" in p:
        score += 15
    if "V17_8B" in p:
        score += 10
    if p.endswith(".CSV"):
        score += 8
    if "CURRENT" in p:
        score += 8

    return score


def extract_from_csv(path: Path, universe: Set[str]) -> List[str]:
    rows, fields = read_csv_dicts(path)
    if not rows or not fields:
        return []
    ticker_col = find_ticker_column(fields)
    if not ticker_col:
        return []

    preferred_fields = [
        c for c in fields
        if any(k in c.lower() for k in (
            "review", "decision", "bucket", "status", "action",
            "label", "category", "candidate", "official", "stage",
            "group", "reason",
        ))
    ]
    if not preferred_fields:
        preferred_fields = fields

    found: List[str] = []
    for row in rows:
        ticker = normalize_ticker(row.get(ticker_col, ""))
        if ticker not in universe:
            continue

        selected_text = " ".join(str(row.get(c, "")) for c in preferred_fields).upper()
        full_text = " ".join(str(v) for v in row.values()).upper()

        include = False

        if "WORTH_REVIEW" in selected_text or "WORTH-REVIEW" in selected_text or "WORTH REVIEW" in selected_text:
            include = True
        if "REVIEW_BUT_LOCKED" in selected_text or "REVIEW BUT LOCKED" in selected_text:
            include = True
        if "OFFICIAL_REVIEW" in selected_text or "OFFICIAL REVIEW" in selected_text:
            include = True
        if "REVIEW" in selected_text and "LOCK" in selected_text:
            include = True

        # If preferred columns missed it, use full row only for very specific tags.
        if not include:
            if "WORTH_REVIEW_BUT_LOCKED" in full_text or "REVIEW_BUT_LOCKED" in full_text:
                include = True

        if include and ticker not in found:
            found.append(ticker)

    # If it selected almost everything, it is probably a repeated global lock status; reject.
    if len(found) > 40:
        return []
    return found


def source_paths(root: Path) -> List[Path]:
    raw17 = root / "outputs" / "v17" / "raw105_decision"
    shadow18 = root / "outputs" / "v18" / "factor_shadow"

    names = [
        raw17 / "V17_8D_CURRENT_RAW105_DECISION_PANEL.txt",
        raw17 / "V17_8D_CURRENT_RAW105_DECISION_PANEL.md",
        raw17 / "V17_8D_READ_FIRST.txt",
        raw17 / "V17_8C_CURRENT_RAW105_DECISION_PANEL.txt",
        raw17 / "V17_8C_CURRENT_RAW105_DECISION_PANEL.md",
        raw17 / "V17_8C_READ_FIRST.txt",
        raw17 / "V17_8B_RAW105_FULL_DECISION_READABLE_PANEL.md",
        raw17 / "V17_8B_RAW105_FULL_DECISION_READABLE_PANEL.txt",
        raw17 / "v17_8B_raw105_decision_readable_panel.csv",
        raw17 / "v17_8A_raw105_full_decision_daily.csv",
        shadow18 / "V18_3B_R2_SHADOW_OFFICIAL_COMPARE_REPORT.md",
        shadow18 / "V18_3B_R2_READ_FIRST.txt",
        shadow18 / "V18_3B_R2_SHADOW_OFFICIAL_COMPARE.csv",
    ]

    # Also add nearby candidates without relying on exact casing.
    for base in (raw17, shadow18):
        if base.exists():
            for p in base.glob("*"):
                up = p.name.upper()
                if not p.is_file():
                    continue
                if not up.endswith((".TXT", ".MD", ".CSV")):
                    continue
                if ("V17_8" in up and ("READ" in up or "PANEL" in up or "DECISION" in up)) or ("V18_3B" in up and ("OFFICIAL" in up or "READ" in up)):
                    names.append(p)

    dedup: List[Path] = []
    seen: Set[str] = set()
    for p in names:
        s = str(p).lower()
        if s not in seen and p.exists():
            dedup.append(p)
            seen.add(s)
    return dedup


def detect_official_review(root: Path, universe: Set[str]) -> Tuple[List[str], str, List[Tuple[str, List[str], int]]]:
    candidates: List[Tuple[Path, List[str], int]] = []

    for path in source_paths(root):
        try:
            if path.suffix.lower() == ".csv":
                names = extract_from_csv(path, universe)
            else:
                names = extract_from_text(path, universe)
        except Exception:
            names = []

        if names:
            candidates.append((path, names, score_candidate_source(path, names)))

    # Choose best source. Avoid tiny partial overlap lines if a real 8-20-name source exists.
    candidates.sort(key=lambda x: x[2], reverse=True)

    if candidates:
        best_path, best_names, _ = candidates[0]
        return best_names, str(best_path), [(str(p), n, s) for p, n, s in candidates[:10]]

    # Last-resort fallback from the strict confirmed V17 locked-10 state used in earlier V18.3B-R2.
    # This is intentionally labeled as fallback and should be replaced by a detected file source.
    fallback = ["ANET", "ARM", "CRWV", "DELL", "FLR", "NET", "QCOM", "SNOW", "VST", "ZS"]
    fallback = [t for t in fallback if t in universe]
    return fallback, "STATIC_FALLBACK_STRICT_CONFIRMED_V17_LOCKED_10", []


def get_col(row: Dict[str, str], candidates: Sequence[str]) -> str:
    lower_map = {k.lower(): k for k in row.keys()}
    for c in candidates:
        if c.lower() in lower_map:
            return str(row.get(lower_map[c.lower()], ""))
    for k in row.keys():
        kl = k.lower()
        if any(c.lower() in kl for c in candidates):
            return str(row.get(k, ""))
    return ""


def make_top30_markdown(rows: List[Dict[str, str]], official: Set[str]) -> str:
    lines: List[str] = []
    lines.append("# V18.3D-R1 Factor Pack Top30")
    lines.append("")
    lines.append(f"Generated: {now_str()}")
    lines.append("")
    lines.append("| rank | ticker | official_review | composite_score | f006 | f007 | f008 | f009 | f011 | f012 |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for i, row in enumerate(rows[:30], start=1):
        t = row.get("_ticker", "")
        official_flag = "YES" if t in official else "NO"
        composite = get_col(row, ["factor_pack_score", "composite_score", "score", "F010_XSEC_COMPOSITE_RANK"])
        f006 = get_col(row, ["F006_SHORT_REV_5D"])
        f007 = get_col(row, ["F007_PULLBACK_IN_UPTREND"])
        f008 = get_col(row, ["F008_VOLUME_ABNORMAL_5_20"])
        f009 = get_col(row, ["F009_VOLUME_PRICE_CONFIRM"])
        f011 = get_col(row, ["F011_TS_MOMENTUM_60_120"])
        f012 = get_col(row, ["F012_TS_PULLBACK_REVERSAL"])
        vals = [composite, f006, f007, f008, f009, f011, f012]
        vals = [str(v).replace("|", "/")[:18] for v in vals]
        lines.append(f"| {i} | {t} | {official_flag} | " + " | ".join(vals) + " |")
    lines.append("")
    return "\n".join(lines)


def write_overlap_csv(path: Path, top30: List[str], official: List[str], ranks: Dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ticker", "shadow_rank", "in_shadow_top30", "in_official_review", "overlap"])
        all_names = []
        for t in top30 + official:
            if t not in all_names:
                all_names.append(t)
        for t in all_names:
            in_shadow = t in top30
            in_official = t in official
            writer.writerow([t, ranks.get(t, ""), "YES" if in_shadow else "NO", "YES" if in_official else "NO", "YES" if in_shadow and in_official else "NO"])


def main() -> int:
    root = root_dir()
    outdir = root / "outputs" / "v18" / "factor_pack"
    outdir.mkdir(parents=True, exist_ok=True)

    try:
        ranking_rows, ranking_tickers, ranking_source = load_ranking(root)
        universe = set(ranking_tickers)
        top30 = ranking_tickers[:30]
        ranks = {t: i for i, t in enumerate(ranking_tickers, start=1)}

        official_names, official_source, diagnostics = detect_official_review(root, universe)
        official_names = [t for t in official_names if t in universe]
        official_set = set(official_names)

        overlap = [t for t in top30 if t in official_set]
        shadow_only = [t for t in top30 if t not in official_set]
        official_not_shadow = [t for t in official_names if t not in set(top30)]

        status = STATUS_OK
        if official_source.startswith("STATIC_FALLBACK"):
            status = STATUS_WARN

        overlap_csv = outdir / "V18_3D_R1_SHADOW_TOP30_OFFICIAL_OVERLAP.csv"
        overlap_md = outdir / "V18_3D_R1_FACTOR_PACK_OFFICIAL_OVERLAP.md"
        top30_md = outdir / "V18_3D_R1_FACTOR_PACK_TOP30.md"
        read_first = outdir / "V18_3D_R1_READ_FIRST.txt"

        write_overlap_csv(overlap_csv, top30, official_names, ranks)
        write_text(top30_md, make_top30_markdown(ranking_rows, official_set))

        md_lines: List[str] = []
        md_lines.append("# V18.3D-R1 Factor Pack Official Overlap")
        md_lines.append("")
        md_lines.append(f"Generated: {now_str()}")
        md_lines.append("")
        md_lines.append(f"- STATUS: `{status}`")
        md_lines.append(f"- RANKING_SOURCE: `{ranking_source}`")
        md_lines.append(f"- OFFICIAL_REVIEW_SOURCE: `{official_source}`")
        md_lines.append(f"- OFFICIAL_REVIEW_COUNT: `{len(official_names)}`")
        md_lines.append(f"- SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: `{len(overlap)}`")
        md_lines.append(f"- SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: `{','.join(overlap) if overlap else 'NONE'}`")
        md_lines.append(f"- SHADOW_TOP30_ONLY_COUNT: `{len(shadow_only)}`")
        md_lines.append(f"- OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: `{len(official_not_shadow)}`")
        md_lines.append("")
        md_lines.append("## Official review names")
        md_lines.append("")
        md_lines.append(", ".join(official_names) if official_names else "NONE")
        md_lines.append("")
        md_lines.append("## Shadow top30 ∩ official review")
        md_lines.append("")
        if overlap:
            md_lines.append("| shadow_rank | ticker |")
            md_lines.append("|---:|---|")
            for t in overlap:
                md_lines.append(f"| {ranks.get(t, '')} | {t} |")
        else:
            md_lines.append("NONE")
        md_lines.append("")
        md_lines.append("## Official review not in shadow top30")
        md_lines.append("")
        md_lines.append(", ".join(official_not_shadow) if official_not_shadow else "NONE")
        md_lines.append("")
        md_lines.append("## Diagnostics: detected candidate sources")
        md_lines.append("")
        if diagnostics:
            md_lines.append("| source | count | score | names |")
            md_lines.append("|---|---:|---:|---|")
            for src, names, score in diagnostics:
                md_lines.append(f"| `{src}` | {len(names)} | {score} | {','.join(names)} |")
        else:
            md_lines.append("No file source detected; static fallback was used.")
        md_lines.append("")
        write_text(overlap_md, "\n".join(md_lines))

        read_lines: List[str] = []
        read_lines.append("=== V18.3D-R1 OFFICIAL OVERLAP FIX ===")
        read_lines.append("")
        read_lines.append(f"V18_3D_R1_STATUS: {status}")
        read_lines.append(f"RUN_TIME: {now_str()}")
        read_lines.append("")
        read_lines.append(f"RANKING_SOURCE: {ranking_source}")
        read_lines.append(f"OFFICIAL_REVIEW_SOURCE: {official_source}")
        read_lines.append(f"OFFICIAL_REVIEW_COUNT: {len(official_names)}")
        read_lines.append(f"OFFICIAL_REVIEW_NAMES: {','.join(official_names) if official_names else 'NONE'}")
        read_lines.append("")
        read_lines.append(f"SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: {len(overlap)}")
        read_lines.append(f"SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: {','.join(overlap) if overlap else 'NONE'}")
        read_lines.append(f"SHADOW_TOP30_ONLY_COUNT: {len(shadow_only)}")
        read_lines.append(f"OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: {len(official_not_shadow)}")
        read_lines.append(f"OFFICIAL_REVIEW_NOT_SHADOW_TOP30_NAMES: {','.join(official_not_shadow) if official_not_shadow else 'NONE'}")
        read_lines.append("")
        read_lines.append("OFFICIAL_DECISION_IMPACT: NONE")
        read_lines.append("PROMOTION_ACTION: NONE")
        read_lines.append("")
        read_lines.append(f"START_HERE: {top30_md}")
        read_lines.append(f"COMPARE_REPORT: {overlap_md}")
        read_lines.append(f"OVERLAP_CSV: {overlap_csv}")
        read_lines.append(f"READ_FIRST: {read_first}")
        read_lines.append("")
        final_text = "\n".join(read_lines)
        write_text(read_first, final_text)

        print(final_text)
        return 0

    except Exception as e:
        fail_text = "\n".join([
            "=== V18.3D-R1 OFFICIAL OVERLAP FIX ===",
            "",
            f"V18_3D_R1_STATUS: {STATUS_FAIL}",
            f"RUN_TIME: {now_str()}",
            f"ERROR: {type(e).__name__}: {e}",
            "",
            "OFFICIAL_DECISION_IMPACT: NONE",
            "PROMOTION_ACTION: NONE",
            "",
        ])
        write_text(outdir / "V18_3D_R1_READ_FIRST.txt", fail_text)
        print(fail_text)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
