from pathlib import Path

path = Path(r"D:\us-tech-quant\scripts\v18\v18_35D_full_universe_factor_technical_recompute.py")
text = path.read_text(encoding="utf-8")

helper = r'''
def load_force_latest_prices(root: Path) -> dict[str, dict[str, str]]:
    force_path = root / "outputs" / "v18" / "price" / "V18_CURRENT_FORCE_YFINANCE_LATEST_PRICES.csv"
    if not force_path.exists():
        return {}

    rows, _ = read_csv(force_path)
    force: dict[str, dict[str, str]] = {}

    for row in rows:
        ticker = str(row.get("ticker", "")).strip().upper()
        status = str(row.get("manual_fetch_status", "")).strip().upper()
        latest_date = str(row.get("manual_latest_price_date", "")).strip()
        latest_close = str(row.get("manual_latest_close", "")).strip()

        if ticker and status == "OK" and latest_date and latest_close:
            force[ticker] = {
                "latest_price_date": latest_date,
                "latest_close": latest_close,
                "latest_price": latest_close,
                "price_data_source": "FORCE_YFINANCE_LATEST",
            }

    return force

'''

if "def load_force_latest_prices(" not in text:
    marker = "\ndef main("
    if marker not in text:
        raise SystemExit("ERROR: cannot find def main() insertion point")
    text = text.replace(marker, "\n" + helper + marker, 1)

if "force_latest_prices = load_force_latest_prices(root)" not in text:
    marker = "    rolling_ledger, _ = read_csv(root / ROLLING_LEDGER)\n"
    if marker not in text:
        raise SystemExit("ERROR: cannot find rolling_ledger read_csv line")
    text = text.replace(
        marker,
        marker + "    force_latest_prices = load_force_latest_prices(root)\n",
        1,
    )

if "FORCE_PRICE_INGEST_R2" not in text:
    lines = text.splitlines()
    out = []
    inserted = False

    for line in lines:
        out.append(line)
        stripped = line.strip()

        if (
            not inserted
            and stripped.startswith("latest_close = ")
            and "existing_factor" in stripped
            and "existing_tech" in stripped
            and "prices[-1]" in stripped
        ):
            indent = line[: len(line) - len(line.lstrip())]
            out.extend([
                "",
                f"{indent}# FORCE_PRICE_INGEST_R2: override stale latest price fields before row construction.",
                f"{indent}force_price = force_latest_prices.get(str(ticker).strip().upper())",
                f"{indent}if force_price:",
                f'{indent}    latest_date = force_price["latest_price_date"]',
                f'{indent}    latest_close = force_price["latest_close"]',
                f'{indent}    price_source = force_price["price_data_source"]',
            ])
            inserted = True

    if not inserted:
        raise SystemExit("ERROR: cannot find latest_close assignment insertion point")

    text = "\n".join(out) + "\n"

path.write_text(text, encoding="utf-8")
print("PATCHED_R2:", path)
