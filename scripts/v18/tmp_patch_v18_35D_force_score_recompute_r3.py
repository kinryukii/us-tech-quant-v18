from pathlib import Path

path = Path(r"D:\us-tech-quant\scripts\v18\v18_35D_full_universe_factor_technical_recompute.py")
text = path.read_text(encoding="utf-8")

# 1) Add helper to inject force latest close into the price history before factor/technical recompute.
helper = r'''
def apply_force_latest_to_prices(prices: list[dict[str, object]], force_price: dict[str, str] | None) -> list[dict[str, object]]:
    if not force_price:
        return prices

    latest_date = str(force_price.get("latest_price_date", "")).strip()
    latest_close = str(force_price.get("latest_close", "")).strip()
    if not latest_date or not latest_close:
        return prices

    out = [dict(row) for row in prices]
    if not out:
        return out

    # If the date already exists, update its close. If not, append a close-only synthetic final bar.
    # We only have latest close from force yfinance output, so open/high/low are set to close and volume is carried forward.
    for row in out:
        if str(row.get("date", "")).strip() == latest_date:
            row["close"] = latest_close
            row["open"] = row.get("open") or latest_close
            row["high"] = row.get("high") or latest_close
            row["low"] = row.get("low") or latest_close
            row["force_price_overlay"] = "TRUE"
            return sorted(out, key=lambda r: str(r.get("date", "")))

    last = dict(out[-1])
    synthetic = {
        "date": latest_date,
        "open": latest_close,
        "high": latest_close,
        "low": latest_close,
        "close": latest_close,
        "volume": last.get("volume", "0") or "0",
        "force_price_overlay": "TRUE",
    }
    out.append(synthetic)
    return sorted(out, key=lambda r: str(r.get("date", "")))

'''

if "def apply_force_latest_to_prices(" not in text:
    marker = "\ndef factor_row("
    if marker not in text:
        raise SystemExit("ERROR: cannot find factor_row insertion point")
    text = text.replace(marker, "\n" + helper + marker, 1)

# 2) Force-covered tickers must not reuse old factor/tech rows; otherwise scores never change.
needle = '''        existing_factor = None if targeted_retry else existing_factor_original
        existing_tech = None if targeted_retry else existing_tech_original
'''

replacement = '''        existing_factor = None if targeted_retry else existing_factor_original
        existing_tech = None if targeted_retry else existing_tech_original

        # FORCE_SCORE_RECOMPUTE_R3: force-covered tickers must recompute factor/technical rows from price history.
        force_price_for_ticker = force_latest_prices.get(str(ticker).strip().upper())
        if force_price_for_ticker:
            existing_factor = None
            existing_tech = None
            evidence.append("FORCE_YFINANCE_LATEST_SCORE_RECOMPUTE_R3")
'''

if "FORCE_SCORE_RECOMPUTE_R3" not in text:
    if needle not in text:
        raise SystemExit("ERROR: cannot find existing_factor/existing_tech assignment block")
    text = text.replace(needle, replacement, 1)

# 3) Inject force price into the prices list before factor_row() and technical_row().
needle2 = '''            if prices:
                evidence.append(price_source)
                if len(prices) >= 120:
'''

replacement2 = '''            if prices:
                force_price_for_ticker = force_latest_prices.get(str(ticker).strip().upper())
                if force_price_for_ticker:
                    prices = apply_force_latest_to_prices(prices, force_price_for_ticker)
                    price_source = "LOCAL_PRICE_CACHE_PLUS_FORCE_YFINANCE_LATEST_CLOSE"
                evidence.append(price_source)
                if len(prices) >= 120:
'''

if "LOCAL_PRICE_CACHE_PLUS_FORCE_YFINANCE_LATEST_CLOSE" not in text:
    if needle2 not in text:
        raise SystemExit("ERROR: cannot find prices branch insertion point")
    text = text.replace(needle2, replacement2, 1)

# 4) Ensure final status/output source reflects force source when used.
needle3 = '''        force_price = force_latest_prices.get(str(ticker).strip().upper())
        if force_price:
            latest_date = force_price["latest_price_date"]
            latest_close = force_price["latest_close"]
            price_source = force_price["price_data_source"]
'''

replacement3 = '''        force_price = force_latest_prices.get(str(ticker).strip().upper())
        if force_price:
            latest_date = force_price["latest_price_date"]
            latest_close = force_price["latest_close"]
            price_source = "LOCAL_PRICE_CACHE_PLUS_FORCE_YFINANCE_LATEST_CLOSE"
'''

if needle3 in text:
    text = text.replace(needle3, replacement3, 1)

path.write_text(text, encoding="utf-8")
print("PATCHED_R3:", path)
