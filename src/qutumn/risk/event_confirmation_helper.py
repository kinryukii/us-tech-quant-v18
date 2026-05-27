from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv
import json

from qutumn.common.paths import STATE_V16, OUTPUTS_V16, ensure_dir


@dataclass
class PendingConfirmationRow:
    confirmation_id: str
    confirmation_datetime_jst: str
    ticker: str
    scope: str
    checked_cpi: str
    checked_nfp: str
    checked_fomc: str
    checked_earnings: str
    checked_company_news: str
    checked_geopolitical: str
    conclusion: str
    restriction: str
    notes: str


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []

    rows: list[dict] = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows


def _ensure_confirmation_log() -> Path:
    path = STATE_V16 / "event_confirmation_log.csv"

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "confirmation_id,confirmation_datetime_jst,ticker,scope,checked_cpi,checked_nfp,checked_fomc,checked_earnings,checked_company_news,checked_geopolitical,conclusion,restriction,notes\n",
            encoding="utf-8-sig",
        )

    return path


def _existing_confirmed_tickers() -> set[str]:
    path = _ensure_confirmation_log()
    rows = _read_csv(path)

    confirmed: set[str] = set()

    for row in rows:
        ticker = str(row.get("ticker", "")).strip().upper()
        confirmation_id = str(row.get("confirmation_id", "")).strip()
        conclusion = str(row.get("conclusion", "")).strip().upper()

        if ticker and confirmation_id and conclusion and conclusion not in {"PENDING", "PENDING_MANUAL_CHECK", "NEEDS_MANUAL_CHECK"}:
            confirmed.add(ticker)

    return confirmed


def build_pending_confirmations() -> tuple[list[PendingConfirmationRow], dict]:
    candidate_path = OUTPUTS_V16 / "review" / "V16_CANDIDATE_REVIEW.csv"
    candidates = _read_csv(candidate_path)

    confirmed_tickers = _existing_confirmed_tickers()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_key = datetime.now().strftime("%Y%m%d")

    pending_rows: list[PendingConfirmationRow] = []

    for row in candidates:
        ticker = str(row.get("ticker", "")).strip().upper()
        review_status = str(row.get("review_status", "")).strip()

        if not ticker:
            continue

        if review_status != "REVIEW_ONLY_CANDIDATE":
            continue

        if ticker in confirmed_tickers:
            continue

        pending_rows.append(
            PendingConfirmationRow(
                confirmation_id=f"EC_PENDING_{date_key}_{ticker}",
                confirmation_datetime_jst=now,
                ticker=ticker,
                scope="TICKER",
                checked_cpi="false",
                checked_nfp="false",
                checked_fomc="false",
                checked_earnings="false",
                checked_company_news="false",
                checked_geopolitical="false",
                conclusion="PENDING_MANUAL_CHECK",
                restriction="HOLD_REVIEW_ONLY",
                notes="Fill manually after checking CPI/NFP/FOMC/earnings/company news/geopolitical risk.",
            )
        )

    summary = {
        "generated_at": now,
        "candidate_count": sum(1 for row in candidates if str(row.get("review_status", "")).strip() == "REVIEW_ONLY_CANDIDATE"),
        "existing_confirmed_count": len(confirmed_tickers),
        "pending_confirmation_count": len(pending_rows),
        "status": "PENDING_CONFIRMATION_ROWS_GENERATED" if pending_rows else "NO_PENDING_CONFIRMATION_REQUIRED",
    }

    return pending_rows, summary


def write_outputs(rows: list[PendingConfirmationRow], summary: dict) -> tuple[Path, Path, Path, Path]:
    out_dir = ensure_dir(OUTPUTS_V16 / "risk")

    pending_state_path = STATE_V16 / "event_confirmation_pending.csv"
    pending_out_path = out_dir / "V16_EVENT_CONFIRMATION_PENDING.csv"
    md_path = out_dir / "V16_EVENT_CONFIRMATION_HELPER.md"
    json_path = out_dir / "V16_EVENT_CONFIRMATION_HELPER.json"

    fieldnames = list(PendingConfirmationRow.__dataclass_fields__.keys())

    for path in [pending_state_path, pending_out_path]:
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row.__dict__)

    lines: list[str] = []
    lines.append("# V16 Event Confirmation Helper")
    lines.append("")
    lines.append(f"生成时间：`{summary.get('generated_at')}`")
    lines.append("")
    lines.append("## 1. 当前结论")
    lines.append("")
    lines.append(f"状态：**{summary.get('status')}**")
    lines.append("")
    lines.append("本页只生成待人工确认模板，不自动判断无事件，不自动放行候选。")
    lines.append("")
    lines.append("## 2. Summary")
    lines.append("")
    lines.append("| item | value |")
    lines.append("|---|---:|")
    lines.append(f"| candidate_count | `{summary.get('candidate_count')}` |")
    lines.append(f"| existing_confirmed_count | `{summary.get('existing_confirmed_count')}` |")
    lines.append(f"| pending_confirmation_count | `{summary.get('pending_confirmation_count')}` |")
    lines.append("")
    lines.append("## 3. Pending Confirmation Rows")
    lines.append("")
    if rows:
        lines.append("| confirmation_id | ticker | conclusion | restriction | notes |")
        lines.append("|---|---|---|---|---|")
        for row in rows:
            lines.append(
                f"| `{row.confirmation_id}` | `{row.ticker}` | `{row.conclusion}` | `{row.restriction}` | {row.notes} |"
            )
    else:
        lines.append("无。")

    lines.append("")
    lines.append("## 4. 人工填写方法")
    lines.append("")
    lines.append("先打开：")
    lines.append("")
    lines.append("`state\\v16\\event_confirmation_pending.csv`")
    lines.append("")
    lines.append("人工确认后，把对应行复制到：")
    lines.append("")
    lines.append("`state\\v16\\event_confirmation_log.csv`")
    lines.append("")
    lines.append("并把字段改成类似：")
    lines.append("")
    lines.append("- checked_cpi = true")
    lines.append("- checked_nfp = true")
    lines.append("- checked_fomc = true")
    lines.append("- checked_earnings = true")
    lines.append("- checked_company_news = true")
    lines.append("- checked_geopolitical = true")
    lines.append("- conclusion = NO_KNOWN_EVENT 或 BLOCK")
    lines.append("- restriction = REVIEW_ONLY 或 FREEZE_NEW_BUYS")
    lines.append("")
    lines.append("## 5. 纪律")
    lines.append("")
    lines.append("在 conclusion 仍为 PENDING_MANUAL_CHECK 时，候选不能升级。")
    lines.append("")
    lines.append("即使人工确认 NO_KNOWN_EVENT，当前也只是 REVIEW_ONLY，不是买入指令。")
    lines.append("")
    lines.append("## 6. 下一步")
    lines.append("")
    lines.append("下一步进入 V16.10E：按 Event Confirmation Workflow 人工确认事件后，重新运行 daily flow。")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "summary": summary,
        "rows": [row.__dict__ for row in rows],
    }

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return md_path, pending_state_path, pending_out_path, json_path


def run_event_confirmation_helper() -> int:
    rows, summary = build_pending_confirmations()
    md_path, pending_state_path, pending_out_path, json_path = write_outputs(rows, summary)

    print("")
    print("V16 event confirmation helper completed.")
    print(f"- status: {summary.get('status')}")
    print(f"- pending: {summary.get('pending_confirmation_count')}")
    print(f"- report: {md_path}")
    print(f"- pending_state: {pending_state_path}")
    print(f"- pending_output: {pending_out_path}")
    print(f"- json: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run_event_confirmation_helper())

