from pathlib import Path

path = Path(r"D:\us-tech-quant\scripts\v18\v18_35D_full_universe_factor_technical_recompute.py")
text = path.read_text(encoding="utf-8")

helper = r'''
def load_force_latest_prices(root: Path) -> dict[str, dict[str, str]]:
    path = root / "outputs" / "v18" / "price" / "V18_CURRENT_FORCE_YFINANCE_LATEST_PRICES.csv"
    if not path.exists():
        return {}

    rows, _ = read_csv(path)
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        ticker = str(row.get("ticker", "")).strip().upper()
        status = str(row.get("manual_fetch_status", "")).strip()
        latest_date = str(row.get("manual_latest_price_date", "")).strip()
        latest_close = str(row.get("manual_latest_close", "")).strip()

        if ticker and status == "OK" and latest_date and latest_close:
            out[ticker] = {
                "latest_price_date": latest_date,
                "latest_close": latest_close,
                "latest_price": latest_close,
                "price_data_source": "FORCE_YFINANCE_LATEST",
            }
    return out

'''

if "def load_force_latest_prices(" not in text:
    marker = "\ndef main("
    if marker not in text:
        raise SystemExit("ERROR: cannot find def main() insertion point")
    text = text.replace(marker, "\n" + helper + marker, 1)

needle = "    rolling_ledger, _ = read_csv(root / ROLLING_LEDGER)\n"
insert = "    rolling_ledger, _ = read_csv(root / ROLLING_LEDGER)\n    force_latest_prices = load_force_latest_prices(root)\n"

if "force_latest_prices = load_force_latest_prices(root)" not in text:
    if needle not in text:
        raise SystemExit("ERROR: cannot find rolling_ledger read insertion point")
    text = text.replace(needle, insert, 1)

needle2 = '''        latest_close = (existing_factor or {}).get("latest_close") or (existing_tech or {}).get("close") or (prices[-1]["close"] if prices else (universe_idx.get(ticker, {}).get("latest_close") or ""))
'''
insert2 = '''        latest_close = (existing_factor or {}).get("latest_close") or (existing_tech or {}).get("close") or (prices[-1]["close"] if prices else (universe_idx.get(ticker, {}).get("latest_close") or ""))

        force_price = force_latest_prices.get(ticker.upper())
        if force_price:
            latest_date = force_price["latest_price_date"]
            latest_close = force_price["latest_close"]
            price_source = force_price["price_data_source"]
'''

if "force_price = force_latest_prices.get(ticker.upper())" not in text:
    if needle2 not in text:
        raise SystemExit("ERROR: cannot find latest_close assignment insertion point")
    text = text.replace(needle2, insert2, 1)

path.write_text(text, encoding="utf-8")
print("PATCHED:", path)
