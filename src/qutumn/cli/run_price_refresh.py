from __future__ import annotations

from qutumn.data.historical_prices import refresh_prices


def main() -> int:
    records, summary = refresh_prices()

    print("")
    print("V16 price refresh completed.")
    print(f"- tickers: {summary.get('ticker_count')}")
    print(f"- refreshed: {summary.get('refreshed_count')}")
    print(f"- fallback: {summary.get('fallback_count')}")
    print(f"- failed: {summary.get('failed_count')}")
    print("- audit: outputs\\v16\\data\\V16_PRICE_REFRESH_AUDIT.md")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
