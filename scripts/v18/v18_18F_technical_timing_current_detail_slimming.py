from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_DRYRUN = "OK_V18_18F_TECHNICAL_TIMING_CURRENT_DETAIL_SLIMMING_AUDIT_READY"
STATUS_APPLY = "OK_V18_18F_TECHNICAL_TIMING_CURRENT_DETAIL_SLIMMING_ARCHIVE_APPLIED"
STATUS_DELETE = "OK_V18_18F_TECHNICAL_TIMING_CURRENT_DETAIL_VERIFIED_ORIGINALS_DELETED"
STATUS_WARN = "WARN_V18_18F_TECHNICAL_TIMING_CURRENT_DETAIL_SLIMMING_VALIDATION_FAILED"
AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"


def parse_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def mb(size: int | float) -> str:
    return f"{float(size) / (1024 * 1024):.3f}"


def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
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
    cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
        f"$p='{ps_path}'; $t=$null; $e=$null; [System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$e) > $null; if ($e.Count -gt 0) {{ $e | ForEach-Object {{ $_.Message }}; exit 1 }}"
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def compile_py(path: Path) -> Tuple[bool, str]:
    try:
        ast.parse(read_text(path), filename=str(path))
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def dangerous_hits(paths: Iterable[Path]) -> List[str]:
    tokens = ["BUY_NOW", "SELL_NOW", "EXECUTE_LIVE_ORDER", "LIVE_TRADE", "LIVE_SELL"]
    hits: List[str] = []
    for path in paths:
        text = read_text(path)
        in_token_block = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            upper = line.upper()
            stripped = upper.strip()
            if "TOKENS =" in upper or "DANGEROUS" in upper:
                in_token_block = True
            safe = (
                "DISABLED" in upper or "DO NOT" in upper or "TOKEN" in upper
                or "HITS.APPEND" in upper or " IN UPPER" in upper or in_token_block
            )
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


def file_set(root: Path) -> set[str]:
    out: set[str] = set()
    for name in ["scripts", "outputs", "state", "archive", "logs", ".venv", ".git", "configs"]:
        base = root / name
        if not base.exists():
            continue
        for dirpath, _, filenames in os.walk(base):
            for filename in filenames:
                p = Path(dirpath) / filename
                try:
                    if p.is_file():
                        out.add(str(p.resolve()))
                except OSError:
                    pass
    return out


def references(root: Path, filename: str, bases: Sequence[str]) -> str:
    refs: List[str] = []
    for base_rel in bases:
        base = root / base_rel
        if not base.exists():
            continue
        for p in base.rglob("*"):
            try:
                if not p.is_file() or p.stat().st_size > 5 * 1024 * 1024:
                    continue
            except OSError:
                continue
            if filename in read_text(p):
                refs.append(rel(root, p))
    return ";".join(sorted(set(refs)))


def csv_profile(path: Path) -> Tuple[int, List[str], Dict[str, str]]:
    row_count = 0
    fields: List[str] = []
    encodings = ("utf-8-sig", "utf-8", "cp932", "latin-1")
    for enc in encodings:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.reader(f)
                fields = next(reader, [])
                for _ in reader:
                    row_count += 1
            break
        except Exception:
            row_count = 0
            fields = []
    lower_map = {c.lower().strip(): c for c in fields}
    required = {
        "ticker": first_col(lower_map, ["ticker", "symbol"]),
        "date": first_col(lower_map, ["date", "trade_date", "price_date", "timestamp"]),
        "strategy": first_col(lower_map, ["strategy", "strategy_name", "mode"]),
        "signal": first_col(lower_map, ["signal", "technical_signal"]),
        "return": first_contains(fields, ["return", "ret_", "excess"]),
        "sharpe": first_contains(fields, ["sharpe"]),
        "max_drawdown": first_contains(fields, ["max_drawdown", "drawdown"]),
        "win_rate": first_contains(fields, ["win_rate", "hit_rate"]),
        "rank": first_contains(fields, ["rank"]),
        "score": first_contains(fields, ["score"]),
        "benchmark": first_contains(fields, ["benchmark", "qqq", "spy", "smh"]),
        "parameter_fields": ";".join([c for c in fields if any(x in c.lower() for x in ["param", "window", "threshold", "lookback", "topn"])][:20]),
    }
    return row_count, fields, required


def first_col(lower_map: Dict[str, str], names: Sequence[str]) -> str:
    for n in names:
        if n in lower_map:
            return lower_map[n]
    return ""


def first_contains(fields: Sequence[str], patterns: Sequence[str]) -> str:
    for c in fields:
        low = c.lower()
        if any(p in low for p in patterns):
            return c
    return ""


def is_detail_like(path: Path, size_bytes: int, row_count: int) -> bool:
    name = path.name.lower()
    detail_terms = ["detail", "raw", "matrix", "grid", "backtest", "result", "expanded", "full", "simulation"]
    summary_terms = ["summary", "report", "read_first", "dashboard"]
    if any(t in name for t in summary_terms) and size_bytes < 5 * 1024 * 1024:
        return False
    return size_bytes >= 25 * 1024 * 1024 or row_count > 10000 or any(t in name for t in detail_terms)


def is_summary_like(path: Path, size_bytes: int, row_count: int) -> bool:
    name = path.name.lower()
    return size_bytes < 5 * 1024 * 1024 and any(t in name for t in ["summary", "report", "read_first", "dashboard", "final"])


def safe_zip_name(path: Path) -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = re.sub(r"[^A-Za-z0-9_.-]+", "__", path.name)
    return f"{base}_{stamp}.zip"


def zip_file(src: Path, dst: Path) -> Tuple[bool, str, int]:
    ensure_dir(dst.parent)
    try:
        with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            zf.write(src, arcname=src.name)
        if not dst.exists() or dst.stat().st_size <= 0:
            return False, "ZIP_NOT_CREATED_OR_EMPTY", 0
        with zipfile.ZipFile(dst, "r") as zf:
            bad = zf.testzip()
            if bad:
                return False, f"ZIP_TEST_FAILED:{bad}", dst.stat().st_size
            if not zf.namelist():
                return False, "ZIP_EMPTY_LISTING", dst.stat().st_size
        return True, "ZIP_VERIFIED", dst.stat().st_size
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}", 0


def build(root: Path, args: argparse.Namespace) -> int:
    root = root.resolve()
    ops = root / "outputs/v18/ops"
    target = root / "outputs/v18/technical_timing_backtest"
    archive_root = root / args.archive_root
    slim_root = root / "outputs/v18/technical_timing_backtest_current_slim"
    ensure_dir(ops)
    apply = bool(args.apply)
    archive_flag = bool(args.archive_large_current_details)
    delete_after = bool(args.delete_original_after_verified_archive)
    mode = "APPLY_DELETE_VERIFIED_ORIGINALS" if apply and archive_flag and delete_after else ("APPLY" if apply else "DRYRUN")

    files_before = file_set(root)
    stable_before = stable_baseline(root)
    current_daily = root / "scripts/v18/run_v18_current_daily_command_center.ps1"
    current_daily_before = sha256(current_daily)

    audit_rows: List[Dict[str, object]] = []
    plan_rows: List[Dict[str, object]] = []
    required_rows: List[Dict[str, object]] = []
    total_bytes = current_bytes = large_current_bytes = detail_bytes = summary_bytes = archive_bytes = 0
    current_count = large_current_count = detail_count = summary_count = archive_count = summary_proposed = 0
    zip_created = zip_verified = summary_created = deleted_count = 0
    zip_created_bytes = deleted_bytes = 0

    threshold = int(args.large_current_file_threshold_mb * 1024 * 1024)
    for p in sorted(target.rglob("*")) if target.exists() else []:
        if not p.is_file():
            continue
        st = p.stat()
        total_bytes += st.st_size
        is_current = "CURRENT" in p.name.upper()
        is_csv = p.suffix.lower() == ".csv"
        is_md = p.suffix.lower() in {".md", ".txt"}
        row_count = 0
        fields: List[str] = []
        required: Dict[str, str] = {}
        if is_csv:
            row_count, fields, required = csv_profile(p)
        detail = is_detail_like(p, st.st_size, row_count)
        summary = is_summary_like(p, st.st_size, row_count)
        large_current = is_current and is_csv and st.st_size >= threshold
        archive_candidate = large_current and detail
        read_refs = references(root, p.name, ["outputs/v18/read_center"])
        report_refs = references(root, p.name, ["outputs/v18/ops", "outputs/v18/technical_timing_backtest"])
        if is_current:
            current_count += 1
            current_bytes += st.st_size
        if large_current:
            large_current_count += 1
            large_current_bytes += st.st_size
        if detail:
            detail_count += 1
            detail_bytes += st.st_size
        if summary:
            summary_count += 1
            summary_bytes += st.st_size
        if archive_candidate:
            archive_count += 1
            archive_bytes += st.st_size
            summary_proposed += 1
        proposed_summary = slim_root / f"{p.stem}_LIGHTWEIGHT_SUMMARY.csv"
        proposed_zip = archive_root / safe_zip_name(p)
        zip_ok = False
        delete_ok = False
        note = ""
        if apply and archive_flag and archive_candidate:
            zip_ok, note, zsize = zip_file(p, proposed_zip)
            if zip_ok:
                zip_created += 1
                zip_verified += 1
                zip_created_bytes += zsize
            if args.keep_lightweight_summary and zip_ok:
                ensure_dir(proposed_summary.parent)
                write_csv(proposed_summary, [{
                    "source_file": rel(root, p), "row_count": row_count, "column_count": len(fields),
                    "columns_sample": ";".join(fields[:50]), "archive_zip": rel(root, proposed_zip),
                    "created_at": dt.datetime.now().isoformat(timespec="seconds"),
                }], ["source_file", "row_count", "column_count", "columns_sample", "archive_zip", "created_at"])
                summary_created += 1
            if zip_ok and delete_after and args.keep_lightweight_summary:
                try:
                    p.unlink()
                    delete_ok = True
                    deleted_count += 1
                    deleted_bytes += st.st_size
                except Exception as exc:
                    note = f"{note}; DELETE_FAILED:{type(exc).__name__}: {exc}"
        audit_rows.append({
            "path": str(p.resolve()), "relative_path": rel(root, p), "file_size_mb": mb(st.st_size),
            "row_count": row_count if is_csv else "", "column_count": len(fields) if is_csv else "",
            "columns_sample": ";".join(fields[:40]), "is_csv": str(is_csv).upper(),
            "is_markdown": str(is_md).upper(), "is_summary_like": str(summary).upper(),
            "is_detail_like": str(detail).upper(), "referenced_by_read_center": str(bool(read_refs)).upper(),
            "referenced_by_report": str(bool(report_refs)).upper(),
            "can_make_lightweight_summary": str(archive_candidate).upper(),
            "proposed_lightweight_summary_path": rel(root, proposed_summary) if archive_candidate else "",
            "proposed_archive_zip_path": rel(root, proposed_zip) if archive_candidate else "",
            "archive_candidate": str(archive_candidate).upper(),
            "delete_original_candidate": str(archive_candidate and zip_ok and delete_after).upper(),
            "protected_reason": "CURRENT_SUMMARY_OR_SMALL_FILE" if is_current and not archive_candidate else "",
            "notes": note or ("Large current detail candidate." if archive_candidate else "Protected or not large detail."),
        })
        if archive_candidate:
            plan_rows.append({
                "source_path": str(p.resolve()), "source_relative_path": rel(root, p),
                "file_size_mb": mb(st.st_size), "row_count": row_count, "column_count": len(fields),
                "proposed_archive_zip_path": rel(root, proposed_zip),
                "proposed_lightweight_summary_path": rel(root, proposed_summary),
                "archive_candidate": "TRUE", "apply": str(apply).upper(),
                "archive_zip_created": str(zip_ok).upper(), "archive_zip_verified": str(zip_ok).upper(),
                "lightweight_summary_created": str(apply and zip_ok and args.keep_lightweight_summary).upper(),
                "delete_original_after_verified_archive": str(delete_after).upper(),
                "original_deleted": str(delete_ok).upper(), "notes": note,
            })
            for key, value in required.items():
                required_rows.append({
                    "source_relative_path": rel(root, p), "field_family": key,
                    "detected_column": value, "present": str(bool(value)).upper(),
                })

    paths = {
        "audit": ops / "V18_18F_CURRENT_TECHNICAL_TIMING_CURRENT_FILE_AUDIT.csv",
        "plan": ops / "V18_18F_CURRENT_TECHNICAL_TIMING_DETAIL_SLIMMING_PLAN.csv",
        "fields": ops / "V18_18F_CURRENT_TECHNICAL_TIMING_DETAIL_REQUIRED_FIELDS_AUDIT.csv",
        "report": ops / "V18_18F_CURRENT_TECHNICAL_TIMING_DETAIL_SLIMMING_REPORT.md",
        "read": ops / "V18_18F_READ_FIRST.txt",
    }
    write_csv(paths["audit"], audit_rows, [
        "path", "relative_path", "file_size_mb", "row_count", "column_count", "columns_sample",
        "is_csv", "is_markdown", "is_summary_like", "is_detail_like", "referenced_by_read_center",
        "referenced_by_report", "can_make_lightweight_summary", "proposed_lightweight_summary_path",
        "proposed_archive_zip_path", "archive_candidate", "delete_original_candidate",
        "protected_reason", "notes",
    ])
    write_csv(paths["plan"], plan_rows, [
        "source_path", "source_relative_path", "file_size_mb", "row_count", "column_count",
        "proposed_archive_zip_path", "proposed_lightweight_summary_path", "archive_candidate",
        "apply", "archive_zip_created", "archive_zip_verified", "lightweight_summary_created",
        "delete_original_after_verified_archive", "original_deleted", "notes",
    ])
    write_csv(paths["fields"], required_rows, ["source_relative_path", "field_family", "detected_column", "present"])
    shutil.copy2(paths["read"], ops / "V18_CURRENT_TECHNICAL_TIMING_DETAIL_SLIMMING_READ_FIRST.txt") if paths["read"].exists() else None
    shutil.copy2(paths["plan"], ops / "V18_CURRENT_TECHNICAL_TIMING_DETAIL_SLIMMING_PLAN.csv")

    files_after = file_set(root)
    deleted_files = files_before - files_after
    new_files = files_after - files_before
    own_outputs = {str(p.resolve()) for p in paths.values()} | {str((ops / "V18_CURRENT_TECHNICAL_TIMING_DETAIL_SLIMMING_PLAN.csv").resolve())}
    source_deleted = sum(1 for f in deleted_files if "/scripts/" in f.replace("\\", "/").lower() or "/configs/" in f.replace("\\", "/").lower())
    alias_deleted = sum(1 for f in deleted_files if "CURRENT" in Path(f).name.upper())
    read_center_deleted = sum(1 for f in deleted_files if "/outputs/v18/read_center/" in f.replace("\\", "/").lower())
    state_deleted = sum(1 for f in deleted_files if "/state/" in f.replace("\\", "/").lower())
    price_deleted = sum(1 for f in deleted_files if "/state/v18/price_cache/" in f.replace("\\", "/").lower())
    stable_deleted = sum(1 for f in deleted_files if "/archive/stable/" in f.replace("\\", "/").lower())
    current_daily_modified = sha256(current_daily) != current_daily_before
    snapshots_modified = stable_modified(stable_before, root)
    ps_ok, _ = parse_ps(root / "scripts/v18/run_v18_18F_technical_timing_current_detail_slimming.ps1")
    py_ok, _ = compile_py(root / "scripts/v18/v18_18F_technical_timing_current_detail_slimming.py")
    hits = dangerous_hits([root / "scripts/v18/run_v18_18F_technical_timing_current_detail_slimming.ps1", root / "scripts/v18/v18_18F_technical_timing_current_detail_slimming.py", *paths.values()])

    status = STATUS_DRYRUN
    if apply and archive_flag and delete_after:
        status = STATUS_DELETE
    elif apply:
        status = STATUS_APPLY
    validations = [
        ps_ok, py_ok, source_deleted == 0, read_center_deleted == 0, state_deleted == 0,
        price_deleted == 0, stable_deleted == 0, not current_daily_modified, not snapshots_modified,
        len(hits) == 0,
    ]
    if not apply:
        validations.extend([deleted_count == 0, zip_created == 0, not deleted_files, len(new_files - own_outputs) == 0])
    validation_fail = sum(1 for ok in validations if not ok)
    if validation_fail:
        status = STATUS_WARN
    values = {
        "STATUS": status, "MODE": mode, "APPLY": str(apply).upper(),
        "ARCHIVE_LARGE_CURRENT_DETAILS": str(archive_flag).upper(),
        "DELETE_ORIGINAL_AFTER_VERIFIED_ARCHIVE": str(delete_after).upper(),
        "TOTAL_BACKTEST_DIR_SIZE_MB": mb(total_bytes),
        "CURRENT_FILE_COUNT": str(current_count), "CURRENT_FILE_MB": mb(current_bytes),
        "LARGE_CURRENT_FILE_COUNT": str(large_current_count), "LARGE_CURRENT_FILE_MB": mb(large_current_bytes),
        "DETAIL_FILE_COUNT": str(detail_count), "DETAIL_FILE_MB": mb(detail_bytes),
        "SUMMARY_FILE_COUNT": str(summary_count), "SUMMARY_FILE_MB": mb(summary_bytes),
        "ARCHIVE_CANDIDATE_COUNT": str(archive_count), "ARCHIVE_CANDIDATE_MB": mb(archive_bytes),
        "ESTIMATED_SAVINGS_MB": mb(archive_bytes if delete_after else 0),
        "LIGHTWEIGHT_SUMMARY_PROPOSED_COUNT": str(summary_proposed),
        "LIGHTWEIGHT_SUMMARY_CREATED_COUNT": str(summary_created),
        "ARCHIVE_ZIP_CREATED_COUNT": str(zip_created),
        "ARCHIVE_ZIP_VERIFIED_COUNT": str(zip_verified),
        "ORIGINAL_DETAIL_DELETED_COUNT": str(deleted_count),
        "ORIGINAL_DETAIL_DELETED_MB": mb(deleted_bytes),
        "SOURCE_CODE_DELETED_COUNT": str(source_deleted),
        "CURRENT_ALIAS_DELETED_COUNT": str(alias_deleted),
        "READ_CENTER_DELETED_COUNT": str(read_center_deleted),
        "STATE_DELETED_COUNT": str(state_deleted),
        "PRICE_CACHE_DELETED_COUNT": str(price_deleted),
        "STABLE_SNAPSHOT_DELETED_COUNT": str(stable_deleted),
        "CURRENT_DAILY_MODIFIED": str(current_daily_modified).upper(),
        "DANGEROUS_TOKEN_FINDING_COUNT": str(len(hits)),
        "VALIDATION_FAIL_COUNT": str(validation_fail),
        "AUTO_TRADE": AUTO_TRADE, "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
    }
    report = [
        "# V18.18F Technical Timing Current Detail Slimming Audit", "",
        "## Summary", "",
        *[f"- {k}: {v}" for k, v in values.items()],
        "", "## Archive Candidates", "",
        *[f"- {r['source_relative_path']}: {r['file_size_mb']} MB, rows={r['row_count']}, columns={r['column_count']}" for r in plan_rows],
        "", "## Safety", "",
        "- DRYRUN creates no archives, no lightweight summaries, and deletes nothing.",
        "- Original current detail files are deleted only with -Apply, archive flag, delete flag, verified zip, and summary creation.",
        "", "## Guardrails", "",
        f"AUTO_TRADE: {AUTO_TRADE}; AUTO_SELL: {AUTO_SELL}; OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}.",
    ]
    write_text(paths["report"], "\n".join(report) + "\n")
    write_text(paths["read"], "\n".join(f"{k}: {v}" for k, v in values.items()) + "\n")
    shutil.copy2(paths["read"], ops / "V18_CURRENT_TECHNICAL_TIMING_DETAIL_SLIMMING_READ_FIRST.txt")

    for key in [
        "STATUS", "MODE", "TOTAL_BACKTEST_DIR_SIZE_MB", "CURRENT_FILE_COUNT", "CURRENT_FILE_MB",
        "LARGE_CURRENT_FILE_COUNT", "LARGE_CURRENT_FILE_MB", "DETAIL_FILE_COUNT", "DETAIL_FILE_MB",
        "SUMMARY_FILE_COUNT", "SUMMARY_FILE_MB", "ARCHIVE_CANDIDATE_COUNT", "ARCHIVE_CANDIDATE_MB",
        "ESTIMATED_SAVINGS_MB", "LIGHTWEIGHT_SUMMARY_PROPOSED_COUNT", "VALIDATION_FAIL_COUNT",
        "AUTO_TRADE", "AUTO_SELL", "OFFICIAL_DECISION_IMPACT",
    ]:
        print(f"{key}: {values[key]}")
    return 0 if validation_fail == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"D:\us-tech-quant")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--archive-large-current-details", type=parse_bool, default=False)
    parser.add_argument("--delete-original-after-verified-archive", action="store_true")
    parser.add_argument("--large-current-file-threshold-mb", type=float, default=25.0)
    parser.add_argument("--keep-lightweight-summary", type=parse_bool, default=True)
    parser.add_argument("--archive-root", default="archive/generated_outputs_compressed/technical_timing_backtest_current_details")
    args = parser.parse_args()
    return build(Path(args.root), args)


if __name__ == "__main__":
    raise SystemExit(main())
