from pathlib import Path
from datetime import datetime
import csv
import json

root = Path(".").resolve()

workflow_md = root / "outputs" / "v16" / "risk" / "V16_EVENT_CONFIRMATION_WORKFLOW.md"
workflow_json = root / "outputs" / "v16" / "risk" / "V16_EVENT_CONFIRMATION_WORKFLOW.json"
to_fill_path = root / "state" / "v16" / "event_confirmation_to_fill.csv"

workflow_json.parent.mkdir(parents=True, exist_ok=True)

to_fill_count = 0
tickers = []

if to_fill_path.exists():
    with to_fill_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            to_fill_count += 1
            ticker = str(row.get("ticker", "")).strip().upper()
            if ticker:
                tickers.append(ticker)

payload = {
    "summary": {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "EVENT_CONFIRMATION_WORKFLOW_READY",
        "to_fill_count": to_fill_count,
        "to_fill_tickers": ";".join(sorted(set(tickers))),
        "to_fill_file": "state\\v16\\event_confirmation_to_fill.csv",
        "workflow_file": "outputs\\v16\\risk\\V16_EVENT_CONFIRMATION_WORKFLOW.md",
        "rule": "Manual event confirmation is required before any candidate can upgrade."
    }
}

workflow_json.write_text(
    json.dumps(payload, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# verify parse immediately
parsed = json.loads(workflow_json.read_text(encoding="utf-8"))
print("workflow json written and verified")
print("status =", parsed["summary"]["status"])
print("to_fill_count =", parsed["summary"]["to_fill_count"])
print("to_fill_tickers =", parsed["summary"]["to_fill_tickers"])
