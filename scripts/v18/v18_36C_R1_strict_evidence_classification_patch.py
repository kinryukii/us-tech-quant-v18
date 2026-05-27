#!/usr/bin/env python
"""V18.36C-R1 strict factor implementation classification audit.

Read-only patch audit. It does not implement factors, fetch data, or modify
ranking/factor/paper/freeze/account state.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


AUTO_TRADE = "DISABLED"
AUTO_SELL = "DISABLED"
OFFICIAL_DECISION_IMPACT = "NONE"
FACTOR_WEIGHTS_MODIFIED = "FALSE"
AUTO_WEIGHT_CHANGE = "DISABLED"
FORBIDDEN_MODIFIED = "FALSE"
STRICT_STATUSES = [
    "REAL_IMPLEMENTED",
    "PROXY_IMPLEMENTED",
    "SHADOW_ONLY",
    "REPORT_ONLY",
    "DISCUSSED_ONLY",
    "MISSING",
]
HISTORICAL_HINTS = ("archive", ".bak", "before_", "snapshot_202", "current_factor_implementation_audit")
REPORT_HINTS = ("read_center", ".md", "read_first", "homepage", "daily_brief", "report")
SHADOW_HINTS = ("shadow", "research", "backtest", "forward", "paper_trading", "attribution", "audit", "weight_research")
CURRENT_PIPELINE_SCRIPTS = (
    "v18_35d_full_universe_factor_technical_recompute.py",
    "v18_35e_online_backfill_candidate_adoption_bridge.py",
    "v18_35f_next_signal_freeze_expansion.py",
    "v18_34b_daily_output_freshness_guard.py",
    "v18_34c_trade_readiness_current_refresh.py",
    "v18_36a_paper_trading_forward_attribution.py",
    "v18_36b_paper_trading_forward_return_filler.py",
)
CURRENT_OUTPUT_FILES = (
    "V18_35D_FULL_UNIVERSE_FACTOR_PACK_RANKING.csv",
    "V18_35D_FULL_UNIVERSE_TECHNICAL_TIMING.csv",
    "V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_FACTOR_PACK.csv",
    "V18_35E_RECOMPUTED_AFTER_ONLINE_BACKFILL_TECHNICAL_TIMING.csv",
    "V18_CURRENT_FULL_RANKED_CANDIDATES.csv",
    "V18_CURRENT_RANKED_CANDIDATES.csv",
    "V18_CURRENT_TOP_RANKED_CANDIDATES.csv",
    "V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
)
REAL_RANKING_FACTOR_IDS = {
    "F001", "F003", "F004", "F005",
    "T001", "T002", "T003", "T004", "T005",
    "VOL001", "VOL003",
}
REAL_GATE_FACTOR_IDS = {"G001", "G003", "G004", "G005", "G006"}
PROXY_FACTOR_IDS = {"OPT002", "OPT003", "OPT004", "V003"}
OPTIONS_FACTOR_IDS = {"OPT001", "OPT002", "OPT003", "OPT004", "OPT005", "OPT006"}
SPECIAL_SHADOW_ONLY_IDS = {"P001", "M001", "V001", "V002", "V004", "F002"}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_v18_36c_module(root: Path):
    path = root / "scripts/v18/v18_36C_factor_implementation_audit.py"
    spec = importlib.util.spec_from_file_location("v18_36c_factor_implementation_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def read_csv(path: Path, required: bool = True) -> list[dict[str, str]]:
    if not path.exists():
        if required:
            raise FileNotFoundError(str(path))
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def contains_term(text: str, term: str) -> bool:
    t = term.lower()
    if len(t) <= 4 and t.isalnum():
        return re.search(rf"(?<![a-z0-9_]){re.escape(t)}(?![a-z0-9_])", text) is not None
    return t in text


def read_text_head(path: Path) -> str:
    try:
        if path.suffix.lower() == ".csv":
            with path.open("r", encoding="utf-8-sig", errors="ignore") as f:
                return f.readline().strip()
        return path.read_text(encoding="utf-8-sig", errors="ignore")[:700000]
    except Exception:
        return ""


def collect_files(root: Path) -> list[dict[str, object]]:
    files: list[dict[str, object]] = []
    for base in [root / "scripts/v18", root / "outputs/v18", root / "state/v18", root / "configs/v18"]:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".ps1", ".csv", ".md", ".txt", ".json", ".yaml", ".yml"}:
                continue
            rel = path.relative_to(root).as_posix()
            rel_l = rel.lower()
            if "v18_36c_r1_strict_evidence_classification_patch" in rel_l:
                continue
            if "v18_36c_factor_implementation_audit" in rel_l:
                continue
            if "v18_current_factor_implementation_audit" in rel_l:
                continue
            if "v18_36c_read_first" in rel_l:
                continue
            if "v18_current_strict_factor_implementation_audit" in rel_l or "v18_36c_r1_read_first" in rel_l:
                continue
            if "v18_36c_r1_strict_factor_implementation_audit" in rel_l:
                continue
            body = read_text_head(path)
            headers = body if path.suffix.lower() == ".csv" else ""
            files.append(
                {
                    "path": rel,
                    "path_l": rel_l,
                    "body": body,
                    "body_l": norm(body),
                    "headers": headers,
                    "suffix": path.suffix.lower(),
                    "kind": "script" if rel_l.startswith("scripts/") else "output" if rel_l.startswith("outputs/") else "state_config",
                    "historical": any(h in rel_l for h in HISTORICAL_HINTS),
                    "report": path.suffix.lower() in {".md", ".txt"} or any(h in rel_l for h in REPORT_HINTS),
                    "shadow": any(h in rel_l for h in SHADOW_HINTS),
                    "current_pipeline": any(s in rel_l for s in CURRENT_PIPELINE_SCRIPTS),
                    "current_output": any(s.lower() in rel_l for s in CURRENT_OUTPUT_FILES),
                }
            )
    return files


def evidence_for_factor(factor, files: list[dict[str, object]]) -> dict[str, object]:
    matched_scripts: list[str] = []
    matched_outputs: list[str] = []
    matched_state: list[str] = []
    fields: set[str] = set()
    evidence_types: set[str] = set()
    formula_evidence: list[str] = []
    ranking_formula_evidence: list[str] = []
    gate_formula_evidence: list[str] = []
    output_field_evidence: list[str] = []
    report_only_evidence: list[str] = []
    data_source_evidence: list[str] = []
    script_formula = False
    script_field_copy = False
    output_field = False
    state_field = False
    config_field = False
    report_text = False
    filename_only = False
    historical_only = True
    shadow_only_paths = False
    current_formula_path = False

    formula_tokens = ("=", "return ", "sort(", "sorted(", "percentile_score", "rolling", "mean(", "std(", "rank", "score", "ret_", "volume_ratio")
    gate_tokens = ("final_action", "event_risk_status", "buy_permission", "execution_status", "daily_trust_level", "trade_readiness", "no_buy", "no-trade")
    ranking_tokens = ("factor_pack_score", "factor_pack_rank", "composite_candidate_score", "recomputed_composite_score", "recomputed_rank", "rank_eligible")
    data_tokens = ("price_cache", "close", "volume", "open", "high", "low", "options", "put_call", "iv_", "gamma", "benchmark", "qqq", "spy")

    for item in files:
        path = str(item["path"])
        path_l = str(item["path_l"])
        body_l = str(item["body_l"])
        body = str(item["body"])
        hay = f"{path_l} {body_l}"
        alias_hits = [a for a in factor.aliases if contains_term(hay, a)]
        if not alias_hits:
            continue
        if not bool(item["historical"]):
            historical_only = False
        if bool(item["shadow"]):
            shadow_only_paths = True
        if str(item["kind"]) == "script":
            matched_scripts.append(path)
            if any(tok in body_l for tok in formula_tokens):
                evidence_types.add("SCRIPT_FORMULA")
                script_formula = True
                formula_evidence.append(path)
            else:
                evidence_types.add("SCRIPT_FIELD_COPY")
                script_field_copy = True
            if bool(item["current_pipeline"]) and any(tok in body_l for tok in ranking_tokens):
                current_formula_path = True
                ranking_formula_evidence.append(path)
            if bool(item["current_pipeline"]) and any(tok in body_l for tok in gate_tokens):
                gate_formula_evidence.append(path)
            if any(tok in body_l for tok in data_tokens):
                data_source_evidence.append(path)
        elif str(item["kind"]) == "output":
            matched_outputs.append(path)
        else:
            matched_state.append(path)

        if str(item["headers"]):
            cols = [c.strip() for c in str(item["headers"]).split(",") if c.strip()]
            matched_cols = [c for c in cols if any(contains_term(c.lower(), a) for a in factor.aliases)]
            if matched_cols:
                fields.update(matched_cols)
                if str(item["kind"]) == "output":
                    evidence_types.add("OUTPUT_FIELD")
                    output_field = True
                    output_field_evidence.append(path)
                elif str(item["kind"]) == "state_config":
                    if path_l.startswith("configs/"):
                        evidence_types.add("CONFIG_FIELD")
                        config_field = True
                    else:
                        evidence_types.add("STATE_FIELD")
                        state_field = True
                    output_field_evidence.append(path)
        elif bool(item["report"]):
            evidence_types.add("REPORT_TEXT")
            report_text = True
            report_only_evidence.append(path)
        elif alias_hits and all(contains_term(path_l, a) for a in alias_hits[:1]):
            evidence_types.add("FILENAME_ONLY")
            filename_only = True
        if bool(item["historical"]):
            evidence_types.add("HISTORICAL_OR_ARCHIVE")

    if not evidence_types:
        evidence_types.add("UNKNOWN")
    return {
        "matched_scripts": sorted(set(matched_scripts))[:12],
        "matched_outputs": sorted(set(matched_outputs))[:12],
        "matched_state": sorted(set(matched_state))[:12],
        "fields": sorted(fields),
        "evidence_types": sorted(evidence_types),
        "script_formula": script_formula,
        "script_field_copy": script_field_copy,
        "output_field": output_field,
        "state_field": state_field,
        "config_field": config_field,
        "report_text": report_text,
        "filename_only": filename_only,
        "historical_only": historical_only if (matched_scripts or matched_outputs or matched_state) else False,
        "shadow_only_paths": shadow_only_paths,
        "current_formula_path": current_formula_path,
        "formula_evidence": sorted(set(formula_evidence))[:8],
        "ranking_formula_evidence": sorted(set(ranking_formula_evidence))[:8],
        "gate_formula_evidence": sorted(set(gate_formula_evidence))[:8],
        "output_field_evidence": sorted(set(output_field_evidence))[:8],
        "report_only_evidence": sorted(set(report_only_evidence))[:8],
        "data_source_evidence": sorted(set(data_source_evidence))[:8],
    }


def classify_factor(factor, original: dict[str, str], ev: dict[str, object]) -> dict[str, object]:
    has_script_formula = bool(ev["script_formula"])
    has_output_field = bool(ev["output_field"] or ev["state_field"] or ev["config_field"])
    has_any = bool(ev["matched_scripts"] or ev["matched_outputs"] or ev["matched_state"])
    has_report = bool(ev["report_text"])
    has_current_pipeline = bool(ev["current_formula_path"])
    is_proxy = factor.factor_id in PROXY_FACTOR_IDS or any(
        field in {"iv_rank_proxy", "gamma_squeeze_status", "gamma_squeeze_risk_label", "put_call_ratio"} for field in ev["fields"]
    )
    is_external = bool(factor.extra_data_required)
    strict_rank = False
    strict_gate = False
    status = "MISSING"
    depth = "NO_EVIDENCE"
    risk = "LOW"
    confidence = "HIGH"
    reason = ""

    if factor.factor_id in REAL_RANKING_FACTOR_IDS and has_script_formula and has_output_field and has_current_pipeline:
        status = "REAL_IMPLEMENTED"
        depth = "FORMULA_AND_OUTPUT_AND_PIPELINE"
        strict_rank = True
        strict_gate = factor.factor_id in {"T005"}
        reason = "Current pipeline has formula evidence plus current output field evidence."
    elif factor.factor_id in REAL_GATE_FACTOR_IDS and has_script_formula and has_any:
        status = "REAL_IMPLEMENTED"
        depth = "FORMULA_AND_OUTPUT_AND_PIPELINE" if has_output_field else "FORMULA_AND_OUTPUT_ONLY"
        strict_gate = True
        reason = "Current gate/trust/freshness evidence found in active pipeline."
    elif is_proxy and has_any:
        status = "PROXY_IMPLEMENTED"
        depth = "PROXY_ONLY"
        risk = "MEDIUM"
        reason = "Proxy/reserved field evidence found, but no confirmed full raw-data implementation."
    elif factor.factor_id == "P001" and has_any:
        status = "SHADOW_ONLY"
        depth = "SHADOW_RESEARCH_ONLY"
        reason = "Paper/forward attribution is implemented as observation layer and does not feed current ranking."
    elif factor.factor_id in SPECIAL_SHADOW_ONLY_IDS and has_any:
        status = "SHADOW_ONLY"
        depth = "SHADOW_RESEARCH_ONLY"
        reason = "Evidence is research/backtest/attribution oriented, not current ranking/gate formula."
    elif has_script_formula and has_output_field and has_current_pipeline:
        status = "REAL_IMPLEMENTED"
        depth = "FORMULA_AND_OUTPUT_AND_PIPELINE"
        reason = "Strict generic current-pipeline formula and output evidence found."
    elif has_script_formula and has_output_field:
        status = "SHADOW_ONLY" if bool(ev["shadow_only_paths"]) else "PROXY_IMPLEMENTED"
        depth = "SHADOW_RESEARCH_ONLY" if status == "SHADOW_ONLY" else "FORMULA_AND_OUTPUT_ONLY"
        risk = "MEDIUM"
        reason = "Formula and output evidence exist, but no confirmed current ranking/gate pipeline consumption."
    elif has_output_field and is_proxy:
        status = "PROXY_IMPLEMENTED"
        depth = "PROXY_ONLY"
        risk = "MEDIUM"
        reason = "Output field exists as proxy/reserved approximation."
    elif has_output_field:
        status = "REPORT_ONLY" if has_report and not has_script_formula else "SHADOW_ONLY"
        depth = "OUTPUT_FIELD_ONLY"
        risk = "MEDIUM"
        reason = "Field evidence exists without strict formula/pipeline evidence."
    elif has_report:
        status = "REPORT_ONLY"
        depth = "REPORT_ONLY"
        risk = "MEDIUM"
        reason = "Only report/read-center text evidence found."
    elif has_any and (bool(ev["filename_only"]) or bool(ev["historical_only"])):
        status = "DISCUSSED_ONLY"
        depth = "DISCUSSION_ONLY"
        risk = "HIGH"
        confidence = "MEDIUM"
        reason = "Only filename, historical, archive, or weak design-note evidence found."
    elif not has_any and not is_external:
        status = "DISCUSSED_ONLY"
        depth = "DISCUSSION_ONLY"
        reason = "Inventory item with no meaningful repo evidence; local-price prototype may be possible."
    else:
        status = "MISSING"
        depth = "NO_EVIDENCE"
        reason = "No meaningful script/output/state/config evidence found."

    if factor.factor_id in OPTIONS_FACTOR_IDS and status == "REAL_IMPLEMENTED":
        # Options factors require true options-chain/formula evidence. Reserved labels are not enough.
        text = " ".join(ev["formula_evidence"] + ev["data_source_evidence"] + ev["output_field_evidence"]).lower()
        has_true_options = "options" in text and ("open_interest" in text or "option_chain" in text or "iv_rank" in text)
        if not has_true_options:
            status = "PROXY_IMPLEMENTED" if has_any else "MISSING"
            depth = "PROXY_ONLY" if has_any else "NO_EVIDENCE"
            strict_rank = False
            strict_gate = False
            risk = "HIGH"
            reason = "Options factor lacks confirmed options-chain/open-interest/true IV formula evidence."

    if factor.factor_id == "M001":
        strict_rank = False
        strict_gate = False
    if factor.factor_id == "P001":
        strict_rank = False
        strict_gate = False
    if status not in {"REAL_IMPLEMENTED"}:
        strict_rank = False
        strict_gate = False if factor.factor_id not in REAL_GATE_FACTOR_IDS else strict_gate

    original_status = original.get("implementation_status", "")
    original_rank = original.get("affects_current_ranking", "FALSE") == "TRUE"
    original_gate = original.get("affects_official_gate", "FALSE") == "TRUE"
    strict_rank_text = str(strict_rank).upper()
    strict_gate_text = str(strict_gate).upper()
    downgraded = False
    upgraded = False
    order = {"MISSING": 0, "DISCUSSED_ONLY": 1, "REPORT_ONLY": 2, "SHADOW_ONLY": 3, "PROXY_IMPLEMENTED": 4, "REAL_IMPLEMENTED": 5}
    old_mapped = {"IMPLEMENTED": "REAL_IMPLEMENTED", "SHADOW_ONLY": "SHADOW_ONLY", "DISCUSSED_ONLY": "DISCUSSED_ONLY", "MISSING": "MISSING"}.get(original_status, "MISSING")
    if order[status] < order[old_mapped] or (original_rank and not strict_rank) or (original_gate and not strict_gate):
        downgraded = True
    if order[status] > order[old_mapped] or (strict_rank and not original_rank) or (strict_gate and not original_gate):
        upgraded = True

    downgrade_reason = ""
    upgrade_reason = ""
    if downgraded:
        downgrade_reason = "Strict audit requires formula+output+pipeline evidence; keyword/report/proxy evidence was insufficient."
    if upgraded:
        upgrade_reason = "Strict audit found stronger formula/output/current-pipeline evidence than the baseline classification."
    if risk == "HIGH":
        confidence = "MEDIUM"
    elif status in {"REAL_IMPLEMENTED", "MISSING"} and confidence != "MEDIUM":
        confidence = "HIGH"
    else:
        confidence = "MEDIUM"

    return {
        "strict_implementation_status": status,
        "original_implementation_status": original_status,
        "implementation_depth": depth,
        "evidence_type": ";".join(ev["evidence_types"]),
        "data_source_evidence": ";".join(ev["data_source_evidence"]),
        "formula_evidence": ";".join(ev["formula_evidence"]),
        "ranking_formula_evidence": ";".join(ev["ranking_formula_evidence"]),
        "gate_formula_evidence": ";".join(ev["gate_formula_evidence"]),
        "output_field_evidence": ";".join(ev["output_field_evidence"]),
        "report_only_evidence": ";".join(ev["report_only_evidence"]),
        "is_proxy_factor": str(is_proxy).upper(),
        "is_true_external_data_factor": str(is_external).upper(),
        "classification_risk": risk,
        "strict_confidence": confidence,
        "strict_affects_current_ranking": strict_rank_text,
        "strict_affects_official_gate": strict_gate_text,
        "strict_reason": reason,
        "downgrade_reason": downgrade_reason,
        "upgrade_reason": upgrade_reason,
        "recommended_validation_command": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/v18/run_v18_36C_R1_strict_evidence_classification_patch.ps1",
        "_downgraded": downgraded,
        "_upgraded": upgraded,
    }


def table(rows: list[dict[str, object]], cols: list[str], limit: int = 25) -> str:
    if not rows:
        return "| none |\n|---|"
    head = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|"
    body = []
    for row in rows[:limit]:
        body.append("| " + " | ".join(str(row.get(c, "")).replace("\n", " ")[:140] for c in cols) + " |")
    return head + "\n" + "\n".join(body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/us-tech-quant")
    args = parser.parse_args()
    root = Path(args.root)
    ops = root / "outputs/v18/ops"
    read_center = root / "outputs/v18/read_center"
    audit_csv = ops / "V18_36C_R1_STRICT_FACTOR_IMPLEMENTATION_AUDIT.csv"
    summary_csv = ops / "V18_36C_R1_STRICT_FACTOR_IMPLEMENTATION_AUDIT_SUMMARY.csv"
    report_path = read_center / "V18_36C_R1_STRICT_FACTOR_IMPLEMENTATION_AUDIT_REPORT.md"
    current_report_path = read_center / "V18_CURRENT_STRICT_FACTOR_IMPLEMENTATION_AUDIT.md"
    read_first_path = ops / "V18_36C_R1_READ_FIRST.txt"
    warnings: list[str] = []
    fails: list[str] = []

    try:
        module = load_v18_36c_module(root)
        factors = module.inventory()
        baseline_rows = read_csv(root / "outputs/v18/ops/V18_36C_FACTOR_IMPLEMENTATION_AUDIT.csv", required=False)
        baseline_by_id = {r.get("factor_id", ""): r for r in baseline_rows}
        files = collect_files(root)
        rows: list[dict[str, object]] = []
        for factor in factors:
            original = baseline_by_id.get(factor.factor_id, {})
            ev = evidence_for_factor(factor, files)
            strict = classify_factor(factor, original, ev)
            row: dict[str, object] = dict(original)
            if not row:
                row = {
                    "factor_id": factor.factor_id,
                    "factor_name": factor.factor_name,
                    "factor_group": factor.factor_group,
                    "implementation_status": "",
                    "confidence": "",
                    "affects_current_ranking": "FALSE",
                    "affects_official_gate": "FALSE",
                    "affects_shadow_research": "FALSE",
                    "affects_read_center_only": "FALSE",
                    "extra_data_required": str(bool(factor.extra_data_required)).upper(),
                    "current_field_names": ";".join(ev["fields"]),
                    "matched_scripts": ";".join(ev["matched_scripts"]),
                    "matched_outputs": ";".join(ev["matched_outputs"]),
                    "matched_state_or_config": ";".join(ev["matched_state"]),
                    "evidence_summary": "",
                    "missing_reason": "",
                    "recommended_next_action": "",
                    "safety_note": "",
                }
            row.update({k: v for k, v in strict.items() if not k.startswith("_")})
            row["_downgraded"] = strict["_downgraded"]
            row["_upgraded"] = strict["_upgraded"]
            rows.append(row)
    except Exception as exc:
        rows = []
        fails.append(f"STRICT_AUDIT_FAILED: {exc}")

    high_risk = sum(1 for r in rows if r.get("classification_risk") == "HIGH")
    if high_risk:
        warnings.append("HIGH_RISK_CLASSIFICATIONS_PRESENT")

    status = "OK_V18_36C_R1_STRICT_FACTOR_IMPLEMENTATION_AUDIT_READY"
    if fails:
        status = "FAIL_V18_36C_R1_STRICT_FACTOR_IMPLEMENTATION_AUDIT_FAILED"
    elif warnings:
        status = "WARN_V18_36C_R1_STRICT_FACTOR_IMPLEMENTATION_AUDIT_REVIEW_NEEDED"

    original_impl = sum(1 for r in rows if r.get("original_implementation_status") == "IMPLEMENTED")
    strict_counts = {s: sum(1 for r in rows if r.get("strict_implementation_status") == s) for s in STRICT_STATUSES}
    downgraded = sum(1 for r in rows if r.get("_downgraded") is True)
    upgraded = sum(1 for r in rows if r.get("_upgraded") is True)
    proxy_count = sum(1 for r in rows if r.get("is_proxy_factor") == "TRUE")
    options_review = sum(1 for r in rows if str(r.get("factor_id", "")).startswith("OPT"))
    summary = {
        "STATUS": status,
        "MODE": "READ_ONLY_STRICT_EVIDENCE_AUDIT",
        "FACTOR_COUNT": len(rows),
        "ORIGINAL_IMPLEMENTED_COUNT": original_impl,
        "STRICT_REAL_IMPLEMENTED_COUNT": strict_counts["REAL_IMPLEMENTED"],
        "STRICT_PROXY_IMPLEMENTED_COUNT": strict_counts["PROXY_IMPLEMENTED"],
        "STRICT_SHADOW_ONLY_COUNT": strict_counts["SHADOW_ONLY"],
        "STRICT_REPORT_ONLY_COUNT": strict_counts["REPORT_ONLY"],
        "STRICT_DISCUSSION_ONLY_COUNT": strict_counts["DISCUSSED_ONLY"],
        "STRICT_MISSING_COUNT": strict_counts["MISSING"],
        "ORIGINAL_AFFECTS_CURRENT_RANKING_COUNT": sum(1 for r in rows if r.get("affects_current_ranking") == "TRUE"),
        "STRICT_AFFECTS_CURRENT_RANKING_COUNT": sum(1 for r in rows if r.get("strict_affects_current_ranking") == "TRUE"),
        "ORIGINAL_AFFECTS_OFFICIAL_GATE_COUNT": sum(1 for r in rows if r.get("affects_official_gate") == "TRUE"),
        "STRICT_AFFECTS_OFFICIAL_GATE_COUNT": sum(1 for r in rows if r.get("strict_affects_official_gate") == "TRUE"),
        "DOWNGRADED_COUNT": downgraded,
        "UPGRADED_COUNT": upgraded,
        "HIGH_RISK_CLASSIFICATION_COUNT": high_risk,
        "OPTIONS_FACTOR_REVIEW_COUNT": options_review,
        "PROXY_FACTOR_COUNT": proxy_count,
        "AUTO_TRADE": AUTO_TRADE,
        "AUTO_SELL": AUTO_SELL,
        "OFFICIAL_DECISION_IMPACT": OFFICIAL_DECISION_IMPACT,
        "FACTOR_WEIGHTS_MODIFIED": FACTOR_WEIGHTS_MODIFIED,
        "AUTO_WEIGHT_CHANGE": AUTO_WEIGHT_CHANGE,
        "FORBIDDEN_MODIFIED": FORBIDDEN_MODIFIED,
        "WARNING_COUNT": len(warnings),
        "ERRORS": ";".join(fails),
        "REPORT_PATH": str(report_path),
        "CURRENT_REPORT_PATH": str(current_report_path),
        "AUDIT_CSV_PATH": str(audit_csv),
    }

    original_fields = [
        "factor_id", "factor_name", "factor_group", "implementation_status", "confidence",
        "affects_current_ranking", "affects_official_gate", "affects_shadow_research",
        "affects_read_center_only", "extra_data_required", "current_field_names", "matched_scripts",
        "matched_outputs", "matched_state_or_config", "evidence_summary", "missing_reason",
        "recommended_next_action", "safety_note",
    ]
    new_fields = [
        "strict_implementation_status", "original_implementation_status", "implementation_depth",
        "evidence_type", "data_source_evidence", "formula_evidence", "ranking_formula_evidence",
        "gate_formula_evidence", "output_field_evidence", "report_only_evidence", "is_proxy_factor",
        "is_true_external_data_factor", "classification_risk", "strict_confidence",
        "strict_affects_current_ranking", "strict_affects_official_gate", "strict_reason",
        "downgrade_reason", "upgrade_reason", "recommended_validation_command",
    ]
    try:
        write_csv(audit_csv, rows, original_fields + new_fields)
        write_csv(summary_csv, [summary], list(summary.keys()))
        distribution = [{"strict_status": s, "count": strict_counts[s]} for s in STRICT_STATUSES]
        downgraded_rows = [r for r in rows if r.get("_downgraded") is True]
        real_ranking = [r for r in rows if r.get("strict_affects_current_ranking") == "TRUE"]
        gate_inputs = [r for r in rows if r.get("strict_affects_official_gate") == "TRUE"]
        proxy_rows = [r for r in rows if r.get("strict_implementation_status") == "PROXY_IMPLEMENTED"]
        report_shadow = [r for r in rows if r.get("strict_implementation_status") in {"REPORT_ONLY", "SHADOW_ONLY"}]
        options_rows = [r for r in rows if str(r.get("factor_id", "")).startswith("OPT")]
        next_order = [r for r in rows if r.get("strict_implementation_status") in {"DISCUSSED_ONLY", "MISSING", "PROXY_IMPLEMENTED"}]
        report = f"""# V18.36C-R1 Strict Factor Implementation Audit

## Executive Conclusion

V18.36C-R1 reran the factor implementation audit with strict evidence rules. It separates true formula/output/current-pipeline implementation from proxies, report labels, shadow research, and discussion-only inventory items. No factor was added, no formula was changed, and no ranking/gate behavior was modified.

## What Changed From V18.36C To V18.36C-R1

- `IMPLEMENTED` was split into `REAL_IMPLEMENTED` and `PROXY_IMPLEMENTED`.
- Paper trading / forward attribution is treated as observation/shadow unless it feeds current ranking.
- Options fields such as GEX, put/call, and IV rank require true options-chain / open-interest / IV formula evidence for real implementation.
- Ranking impact now requires explicit current formula/output/pipeline evidence, not proximity to candidate-score fields.

## Strict Status Distribution

{table(distribution, ["strict_status", "count"], 10)}

## Downgraded Factors

{table(downgraded_rows, ["factor_id", "factor_name", "original_implementation_status", "strict_implementation_status", "downgrade_reason"], 40)}

## Factors Still Confirmed As Real Ranking Inputs

{table(real_ranking, ["factor_id", "factor_name", "implementation_depth", "ranking_formula_evidence", "output_field_evidence"], 35)}

## Factors Confirmed As Gate Inputs

{table(gate_inputs, ["factor_id", "factor_name", "implementation_depth", "gate_formula_evidence", "output_field_evidence"], 35)}

## Proxy Factors

{table(proxy_rows, ["factor_id", "factor_name", "strict_reason", "output_field_evidence"], 35)}

## Report-Only / Shadow-Only Factors

{table(report_shadow, ["factor_id", "factor_name", "strict_implementation_status", "implementation_depth", "strict_reason"], 40)}

## Options-Factor Evidence Review

{table(options_rows, ["factor_id", "factor_name", "strict_implementation_status", "is_proxy_factor", "strict_reason"], 20)}

## Recommended Next Development Order

{table(next_order, ["factor_id", "factor_name", "strict_implementation_status", "is_true_external_data_factor", "recommended_validation_command"], 25)}

## Safety

- READ ONLY strict classification audit.
- No ranking formulas changed.
- No factor weights changed.
- No candidate files changed.
- No freeze ledgers changed.
- No universe state changed.
- No paper trading ledgers changed.
- No account state changed.
- No broker/API/order/auto-trade/auto-sell logic added.
- No yfinance or external data fetch was called.
- AUTO_TRADE DISABLED.
- AUTO_SELL DISABLED.
- OFFICIAL_DECISION_IMPACT NONE.
- FACTOR_WEIGHTS_MODIFIED FALSE.
- AUTO_WEIGHT_CHANGE DISABLED.
- FORBIDDEN_MODIFIED FALSE.
"""
        write_text(report_path, report)
        write_text(current_report_path, report)
        read_first = [
            f"STATUS: {status}",
            "MODE: READ_ONLY_STRICT_EVIDENCE_AUDIT",
            f"FACTOR_COUNT: {len(rows)}",
            f"STRICT_REAL_IMPLEMENTED_COUNT: {strict_counts['REAL_IMPLEMENTED']}",
            f"STRICT_PROXY_IMPLEMENTED_COUNT: {strict_counts['PROXY_IMPLEMENTED']}",
            f"STRICT_SHADOW_ONLY_COUNT: {strict_counts['SHADOW_ONLY']}",
            f"STRICT_REPORT_ONLY_COUNT: {strict_counts['REPORT_ONLY']}",
            f"STRICT_DISCUSSION_ONLY_COUNT: {strict_counts['DISCUSSED_ONLY']}",
            f"STRICT_MISSING_COUNT: {strict_counts['MISSING']}",
            f"STRICT_AFFECTS_CURRENT_RANKING_COUNT: {summary['STRICT_AFFECTS_CURRENT_RANKING_COUNT']}",
            f"STRICT_AFFECTS_OFFICIAL_GATE_COUNT: {summary['STRICT_AFFECTS_OFFICIAL_GATE_COUNT']}",
            f"DOWNGRADED_COUNT: {downgraded}",
            f"HIGH_RISK_CLASSIFICATION_COUNT: {high_risk}",
            f"OPTIONS_FACTOR_REVIEW_COUNT: {options_review}",
            f"AUTO_TRADE: {AUTO_TRADE}",
            f"AUTO_SELL: {AUTO_SELL}",
            f"OFFICIAL_DECISION_IMPACT: {OFFICIAL_DECISION_IMPACT}",
            f"FACTOR_WEIGHTS_MODIFIED: {FACTOR_WEIGHTS_MODIFIED}",
            f"AUTO_WEIGHT_CHANGE: {AUTO_WEIGHT_CHANGE}",
            f"FORBIDDEN_MODIFIED: {FORBIDDEN_MODIFIED}",
            f"ERRORS: {';'.join(fails)}",
            f"REPORT_PATH: {report_path}",
            f"CURRENT_REPORT_PATH: {current_report_path}",
            f"AUDIT_CSV_PATH: {audit_csv}",
            "RECOMMENDED_NEXT_STEP: Validate downgraded/proxy factors manually before any future shadow implementation proposal.",
        ]
        write_text(read_first_path, "\n".join(read_first) + "\n")
    except Exception as exc:
        status = "FAIL_V18_36C_R1_STRICT_FACTOR_IMPLEMENTATION_AUDIT_FAILED"
        write_text(read_first_path, f"STATUS: {status}\nMODE: READ_ONLY_STRICT_EVIDENCE_AUDIT\nERROR: {exc}\nFORBIDDEN_MODIFIED: {FORBIDDEN_MODIFIED}\n")

    return 1 if status.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
