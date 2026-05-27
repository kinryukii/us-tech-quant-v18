# V18_CURRENT_DATA_FRESHNESS

- Current price audit: outputs/v18/data/V18_CURRENT_SCAN_SCOPED_PRICE_UPDATE_AUDIT.csv
- Event audit: outputs/v18/risk/V18_CURRENT_SCAN_SCOPED_EVENT_UPDATE_AUDIT.csv
- Selected rows: 318
- Local cache used rows: 318
- yfinance used rows: 0
- Cache-only rows: 318
- Failed price rows: 0
- Selected update mode(s): LOCAL_CACHE_ONLY_SAFE_MODE
- Selected update status(es): CACHE_ONLY
- Latest price date range observed: 2026-05-14 -> 2026-05-22
- Command-center source used: outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt
- Command-center source status: OK
- Current mode source used: outputs/v18/read_center/V18_CURRENT_READ_FIRST.txt
- Current mode source status: OK

## Provider Condition

- yfinance cache preflight pass/fail: PASS
- yfinance preflight failures: 0
- cache repair failures: 0
- local cache bootstrap rows already present: 102
- local cache bootstrap rows with cache after: 103
- event provider safe-mode rows: 318
- event provider no-provider rows: 318
- event audit source available: YES
- event audit sentence: Primary event audit was found at outputs/v18/risk/V18_CURRENT_SCAN_SCOPED_EVENT_UPDATE_AUDIT.csv.

## Human Explanation

The current run is cache-backed and safe-mode friendly, but it is not a clean live-provider refresh. Historical yfinance preflight/caching audits show failures, while the current selected universe refresh stayed on local-cache-only paths.
